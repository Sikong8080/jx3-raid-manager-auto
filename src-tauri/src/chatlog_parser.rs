use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use std::path::Path;

/// 聊天记录数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatlogRecord {
    pub time: i64,
    pub text: String,
    pub msg: String,
}

/// 扫描请求参数
#[derive(Debug, Deserialize)]
pub struct ScanRequest {
    pub game_directory: String,
    pub role_name: String,
    pub time_start: i64,
    pub time_end: i64,
}

/// 扫描结果
#[derive(Debug, Serialize)]
pub struct ScanResult {
    pub success: bool,
    pub records: Vec<ChatlogRecord>,
    pub chatlog_path: Option<String>,
    pub error: Option<String>,
    pub debug_info: Vec<String>,
}

/// 查找chatlog.db路径结果
#[derive(Debug, Serialize)]
pub struct FindPathResult {
    pub success: bool,
    pub path: Option<String>,
    pub error: Option<String>,
    pub debug_info: Vec<String>,
}

/// 查找角色对应的chat_log目录路径
/// 
/// 正确路径结构: 
/// - {gameDir}/bin/zhcn_hd/interface/MY#DATA/{数字ID}@zhcn_hd/{角色名}/ (角色标识)
/// - {gameDir}/bin/zhcn_hd/interface/MY#DATA/{数字ID}@zhcn_hd/userdata/chat_log/ (聊天记录)
/// - {gameDir}/interface/MY#DATA/... (如果gameDir已包含bin/zhcn_hd)
#[tauri::command]
pub fn find_chatlog_path(game_directory: String, role_name: String) -> Result<String, String> {
    let result = find_chatlog_path_internal(&game_directory, &role_name);
    serde_json::to_string(&result).map_err(|e| e.to_string())
}

fn find_chatlog_path_internal(game_directory: &str, role_name: &str) -> FindPathResult {
    let mut debug_info = Vec::new();
    
    debug_info.push(format!("游戏目录: {}", game_directory));
    debug_info.push(format!("查找角色: {}", role_name));
    
    // 尝试多种可能的基础路径（按优先级排序）
    let possible_bases = vec![
        // 1. 直接在 gameDir 下查找 interface/my#data（gameDir 可能已经是 D:\JX3\bin\zhcn_hd）
        std::path::Path::new(game_directory)
            .join("interface").join("MY#DATA"),
        std::path::Path::new(game_directory)
            .join("interface").join("my#data"),
        // 2. gameDir 是 D:\JX3，需要加上 bin/zhcn_hd
        std::path::Path::new(game_directory)
            .join("bin").join("zhcn_hd").join("interface").join("MY#DATA"),
        std::path::Path::new(game_directory)
            .join("bin").join("zhcn_hd").join("interface").join("my#data"),
        // 3. gameDir 是 D:\JX3，完整路径包含 Game/JX3
        std::path::Path::new(game_directory)
            .join("Game").join("JX3").join("bin").join("zhcn_hd").join("interface").join("MY#DATA"),
        std::path::Path::new(game_directory)
            .join("Game").join("JX3").join("bin").join("zhcn_hd").join("interface").join("my#data"),
    ];
    
    for my_data_path in possible_bases {
        debug_info.push(format!("检查路径: {:?}", my_data_path));
        
        if !my_data_path.exists() {
            debug_info.push(format!("  不存在"));
            continue;
        }
        
        debug_info.push(format!("  存在! 开始扫描子目录"));
        
        // 遍历 MY#DATA 下的所有 @zhcn_hd 目录
        let entries = match std::fs::read_dir(&my_data_path) {
            Ok(entries) => entries,
            Err(e) => {
                debug_info.push(format!("  无法读取: {}", e));
                continue;
            }
        };
        
        for entry in entries.flatten() {
            let dir_name = entry.file_name().to_string_lossy().to_string();
            let user_dir = entry.path();
            
            // 只处理 @zhcn_hd 结尾的目录
            if !dir_name.to_lowercase().ends_with("@zhcn_hd") {
                continue;
            }
            
            debug_info.push(format!("  检查用户目录: {}", dir_name));
            
            // 检查该用户目录下是否有角色名子目录
            if let Ok(sub_entries) = std::fs::read_dir(&user_dir) {
                let sub_dirs: Vec<String> = sub_entries
                    .flatten()
                    .filter(|e| e.path().is_dir())
                    .map(|e| e.file_name().to_string_lossy().to_string())
                    .collect();
                
                // 检查是否有匹配的角色名
                if sub_dirs.iter().any(|name| name == role_name) {
                    debug_info.push(format!("    ✓ 找到角色目录: {}", role_name));
                    
                    // 检查 userdata/chat_log 是否存在
                    let chat_log_path = user_dir.join("userdata").join("chat_log");
                    
                    if chat_log_path.exists() {
                        debug_info.push(format!("    ✓ chat_log目录存在: {:?}", chat_log_path));
                        return FindPathResult {
                            success: true,
                            path: Some(chat_log_path.to_string_lossy().to_string()),
                            error: None,
                            debug_info,
                        };
                    } else {
                        debug_info.push(format!("    ✗ chat_log目录不存在: {:?}", chat_log_path));
                    }
                } else {
                    debug_info.push(format!("    子目录: {:?}", sub_dirs));
                    debug_info.push(format!("    未找到角色 '{}'", role_name));
                }
            }
        }
    }
    
    // 未找到
    FindPathResult {
        success: false,
        path: None,
        error: Some(format!("未找到角色 {} 对应的聊天日志目录", role_name)),
        debug_info,
    }
}

/// 扫描指定角色的聊天日志
/// 
/// 从 chat_log 目录下的所有 .db 文件中读取聊天记录
#[tauri::command]
pub fn scan_chatlog_for_role(request: String) -> Result<String, String> {
    let req: ScanRequest = serde_json::from_str(&request)
        .map_err(|e| format!("解析请求失败: {}", e))?;
    
    let result = scan_chatlog_internal(&req);
    serde_json::to_string(&result).map_err(|e| e.to_string())
}

fn scan_chatlog_internal(req: &ScanRequest) -> ScanResult {
    let mut debug_info = Vec::new();
    
    // 1. 查找 chat_log 目录路径
    let path_result = find_chatlog_path_internal(&req.game_directory, &req.role_name);
    debug_info.extend(path_result.debug_info);
    
    if !path_result.success {
        return ScanResult {
            success: false,
            records: vec![],
            chatlog_path: None,
            error: path_result.error,
            debug_info,
        };
    }
    
    let chat_log_dir = path_result.path.unwrap();
    debug_info.push(format!("chat_log目录: {}", chat_log_dir));
    
    // 2. 扫描目录下的所有 .db 文件
    let chat_log_path = Path::new(&chat_log_dir);
    let db_files: Vec<_> = match std::fs::read_dir(chat_log_path) {
        Ok(entries) => entries
            .flatten()
            .filter(|e| {
                e.path().extension()
                    .map(|ext| ext.to_string_lossy().to_lowercase() == "db")
                    .unwrap_or(false)
            })
            .map(|e| e.path())
            .collect(),
        Err(e) => {
            debug_info.push(format!("无法读取chat_log目录: {}", e));
            return ScanResult {
                success: false,
                records: vec![],
                chatlog_path: Some(chat_log_dir),
                error: Some(format!("无法读取chat_log目录: {}", e)),
                debug_info,
            };
        }
    };
    
    debug_info.push(format!("找到 {} 个.db文件", db_files.len()));
    
    if db_files.is_empty() {
        return ScanResult {
            success: false,
            records: vec![],
            chatlog_path: Some(chat_log_dir),
            error: Some("chat_log目录下没有.db文件".to_string()),
            debug_info,
        };
    }
    
    // 3. 从所有 .db 文件中读取聊天记录
    let mut all_records = Vec::new();
    
    for db_path in &db_files {
        debug_info.push(format!("读取: {}", db_path.file_name().unwrap_or_default().to_string_lossy()));
        
        match Connection::open(db_path) {
            Ok(conn) => {
                match read_chatlog_records(&conn, req.time_start, req.time_end) {
                    Ok(records) => {
                        debug_info.push(format!("  读取到 {} 条记录", records.len()));
                        all_records.extend(records);
                    }
                    Err(e) => {
                        debug_info.push(format!("  查询失败: {}", e));
                    }
                }
            }
            Err(e) => {
                debug_info.push(format!("  打开失败: {}", e));
            }
        }
    }
    
    // 按时间排序
    all_records.sort_by_key(|r| r.time);
    
    debug_info.push(format!("总共读取到 {} 条记录", all_records.len()));
    
    ScanResult {
        success: true,
        records: all_records,
        chatlog_path: Some(chat_log_dir),
        error: None,
        debug_info,
    }
}

/// 从数据库读取聊天记录
fn read_chatlog_records(
    conn: &Connection,
    time_start: i64,
    time_end: i64,
) -> Result<Vec<ChatlogRecord>, rusqlite::Error> {
    // chatlog表结构: time, text, msg
    let mut stmt = conn.prepare(
        "SELECT time, text, msg FROM chatlog WHERE time >= ? AND time <= ? ORDER BY time ASC"
    )?;
    
    let records = stmt.query_map([time_start, time_end], |row| {
        Ok(ChatlogRecord {
            time: row.get(0)?,
            text: row.get::<_, String>(1).unwrap_or_default(),
            msg: row.get::<_, String>(2).unwrap_or_default(),
        })
    })?;
    
    let mut result = Vec::new();
    for record in records {
        if let Ok(r) = record {
            result.push(r);
        }
    }
    
    Ok(result)
}

/// 扫描所有可用的chat_log目录
#[tauri::command]
pub fn list_available_chatlogs(game_directory: String) -> Result<String, String> {
    let possible_bases = vec![
        std::path::Path::new(&game_directory)
            .join("Game").join("JX3").join("bin").join("zhcn_hd").join("interface").join("MY#DATA"),
        std::path::Path::new(&game_directory)
            .join("bin").join("zhcn_hd").join("interface").join("MY#DATA"),
    ];
    
    let mut chatlog_paths = Vec::new();
    
    for my_data_path in possible_bases {
        if !my_data_path.exists() {
            continue;
        }
        
        if let Ok(entries) = std::fs::read_dir(&my_data_path) {
            for entry in entries.flatten() {
                let user_dir = entry.path();
                
                // 检查直接子目录
                let chat_log_path = user_dir.join("userdata").join("chat_log");
                if chat_log_path.exists() {
                    chatlog_paths.push(chat_log_path.to_string_lossy().to_string());
                }
                
                // 检查 @zhcn_hd 目录下的子目录
                if entry.file_name().to_string_lossy().ends_with("@zhcn_hd") {
                    if let Ok(sub_entries) = std::fs::read_dir(&user_dir) {
                        for sub_entry in sub_entries.flatten() {
                            let sub_chat_log = sub_entry.path().join("userdata").join("chat_log");
                            if sub_chat_log.exists() {
                                chatlog_paths.push(sub_chat_log.to_string_lossy().to_string());
                            }
                        }
                    }
                }
            }
        }
    }
    
    serde_json::to_string(&chatlog_paths).map_err(|e| e.to_string())
}

/// 直接从指定路径读取聊天日志
#[tauri::command]
pub fn read_chatlog_from_path(
    chatlog_path: String,
    time_start: i64,
    time_end: i64,
) -> Result<String, String> {
    let path = Path::new(&chatlog_path);
    
    // 如果是目录，扫描所有 .db 文件
    if path.is_dir() {
        let mut all_records = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(path) {
            for entry in entries.flatten() {
                let file_path = entry.path();
                if file_path.extension().map(|e| e == "db").unwrap_or(false) {
                    if let Ok(conn) = Connection::open(&file_path) {
                        if let Ok(records) = read_chatlog_records(&conn, time_start, time_end) {
                            all_records.extend(records);
                        }
                    }
                }
            }
        }
        
        all_records.sort_by_key(|r| r.time);
        return serde_json::to_string(&all_records).map_err(|e| e.to_string());
    }
    
    // 如果是文件
    if !path.exists() {
        return Err(format!("聊天日志文件不存在: {}", chatlog_path));
    }
    
    let conn = Connection::open(path)
        .map_err(|e| format!("无法打开数据库: {}", e))?;
    
    let records = read_chatlog_records(&conn, time_start, time_end)
        .map_err(|e| format!("查询失败: {}", e))?;
    
    serde_json::to_string(&records).map_err(|e| e.to_string())
}
