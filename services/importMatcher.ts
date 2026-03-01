/**
 * 导入匹配引擎
 * 将GKP文件与聊天日志进行时间匹配，生成导入建议
 */

import { ImportSuggestion } from '../types';
import { GkpFileInfo } from './gkpDirectoryScanner';
import {
  scanChatlogForRole,
  expandTimeRange,
  msToSeconds,
} from './chatlogScanner';
import {
  aggregateGoldFromRecords,
  calculateConfidence,
  isRecordRelatedToRole,
} from '../utils/goldParser';
import { generateUUID } from '../utils/uuid';

/**
 * 匹配选项
 */
export interface MatchOptions {
  gameDirectory: string;
  roleName: string;
  /** 时间范围扩展分钟数，默认30分钟 */
  marginMinutes?: number;
  /** 最大返回建议数量，默认10条 */
  maxSuggestions?: number;
  /** 最小置信度阈值，默认0.1 */
  minConfidence?: number;
}

/**
 * 匹配结果
 */
export interface MatchResult {
  success: boolean;
  suggestions: ImportSuggestion[];
  error?: string;
  scanLogs?: string[];
}

/**
 * 将GKP文件与聊天日志进行匹配
 * 生成导入建议列表
 */
export async function matchGkpWithChatlog(
  gkpFiles: GkpFileInfo[],
  options: MatchOptions
): Promise<MatchResult> {
  const {
    gameDirectory,
    roleName,
    marginMinutes = 30,
    maxSuggestions = 10,
    minConfidence = 0.1,
  } = options;
  
  const suggestions: ImportSuggestion[] = [];
  const scanLogs: string[] = [];
  
  scanLogs.push(`[匹配] 游戏目录: ${gameDirectory}`);
  scanLogs.push(`[匹配] 角色名: ${roleName}`);
  scanLogs.push(`[匹配] 时间扩展: ±${marginMinutes}分钟`);
  scanLogs.push(`[匹配] 待处理GKP文件数: ${gkpFiles.length}`);
  
  // 按时间倒序排列GKP文件（最新的在前）
  const sortedGkpFiles = [...gkpFiles].sort((a, b) => b.timestamp - a.timestamp);
  
  // 限制处理数量
  const filesToProcess = sortedGkpFiles.slice(0, maxSuggestions * 2);
  
  for (const gkpFile of filesToProcess) {
    try {
      // GKP时间戳是毫秒，转换为秒
      const gkpStartSeconds = msToSeconds(gkpFile.timestamp);
      
      // 计算查询时间范围
      const [timeStart, timeEnd] = expandTimeRange(
        gkpStartSeconds,
        undefined, // 没有结束时间，使用默认的开始时间+2小时
        marginMinutes
      );
      
      scanLogs.push(`---`);
      scanLogs.push(`[扫描] ${gkpFile.mapName} (${gkpFile.playerCount}人)`);
      scanLogs.push(`  文件: ${gkpFile.fileName}`);
      scanLogs.push(`  GKP时间: ${new Date(gkpFile.timestamp).toLocaleString()}`);
      scanLogs.push(`  查询范围: ${new Date(timeStart * 1000).toLocaleString()} ~ ${new Date(timeEnd * 1000).toLocaleString()}`);
      
      // 扫描聊天日志
      const scanResult = await scanChatlogForRole({
        gameDirectory,
        roleName,
        timeStart,
        timeEnd,
      });
      
      if (!scanResult.success) {
        scanLogs.push(`  ⚠ chatlog扫描失败: ${scanResult.error}`);
        // 添加调试信息
        if (scanResult.debugInfo && scanResult.debugInfo.length > 0) {
          scanLogs.push(`  调试信息:`);
          scanResult.debugInfo.forEach(info => scanLogs.push(`    ${info}`));
        }
        continue;
      }
      
      if (scanResult.chatlogPath) {
        scanLogs.push(`  chat_log目录: ${scanResult.chatlogPath}`);
      }
      
      const chatRecords = scanResult.records;
      scanLogs.push(`  聊天记录数: ${chatRecords.length}`);
      
      if (chatRecords.length === 0) {
        scanLogs.push(`  跳过（无聊天记录）`);
        continue;
      }
      
      // 过滤出与当前角色相关的金币记录（个人收入+个人支出）
      const goldRecords = chatRecords.filter(r => 
        isRecordRelatedToRole(r.text, roleName, r.msg)
      );
      scanLogs.push(`  与角色相关的金币记录: ${goldRecords.length}条`);
      
      // 打印前3条金币相关记录作为样例
      goldRecords.slice(0, 3).forEach((r, i) => {
        const preview = (r.text || r.msg).substring(0, 50);
        scanLogs.push(`    样例${i + 1}: ${preview}...`);
      });
      
      // 解析金币信息（从msg字段提取个人收入，从text字段提取个人支出）
      const goldInfo = aggregateGoldFromRecords(chatRecords, roleName);
      
      // 计算置信度
      const confidence = calculateConfidence(
        chatRecords.length,
        goldInfo.incomeRecords.length,
        goldInfo.totalIncome
      );
      
      scanLogs.push(`  个人收入: ${goldInfo.totalIncome}金 (${goldInfo.incomeRecords.length}笔), 个人支出: ${goldInfo.totalExpense}金 (${goldInfo.expenseRecords.length}笔)`);
      scanLogs.push(`  置信度: ${(confidence * 100).toFixed(0)}%`);
      
      // 如果置信度太低，跳过
      if (confidence < minConfidence) {
        scanLogs.push(`  跳过（置信度 ${(confidence * 100).toFixed(0)}% < 阈值 ${(minConfidence * 100).toFixed(0)}%）`);
        continue;
      }
      
      // 构建导入建议
      const suggestion: ImportSuggestion = {
        id: generateUUID(),
        gkpFileName: gkpFile.fileName,
        gkpFilePath: gkpFile.filePath,
        raidName: gkpFile.mapName,
        playerCount: gkpFile.playerCount,
        difficulty: gkpFile.difficulty,
        timestamp: gkpFile.timestamp,
        roleName: gkpFile.roleName,
        goldIncome: goldInfo.totalIncome,
        goldExpense: goldInfo.totalExpense,
        confidence,
        matchedChatCount: chatRecords.length,
        chatRecords: goldRecords.slice(0, 20), // 只保留前20条金币相关记录
      };
      
      suggestions.push(suggestion);
      scanLogs.push(`  ✓ 已添加到建议列表`);
      
      // 达到最大数量后停止
      if (suggestions.length >= maxSuggestions) {
        scanLogs.push(`[匹配] 已达到最大建议数 ${maxSuggestions}，停止处理`);
        break;
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      scanLogs.push(`  ✗ 处理异常: ${errorMsg}`);
    }
  }
  
  scanLogs.push(`---`);
  scanLogs.push(`[匹配] 最终生成 ${suggestions.length} 条建议`);
  
  // 按置信度排序
  suggestions.sort((a, b) => b.confidence - a.confidence);
  
  return {
    success: true,
    suggestions,
    scanLogs,
  };
}

/**
 * 根据角色筛选GKP文件
 * 只返回与指定角色匹配的文件
 */
export function filterGkpFilesByRole(
  gkpFiles: GkpFileInfo[],
  roleName: string
): GkpFileInfo[] {
  return gkpFiles.filter(file => 
    !file.roleName || file.roleName === roleName
  );
}

/**
 * 根据时间范围筛选GKP文件
 * @param gkpFiles GKP文件列表
 * @param startTime 开始时间（毫秒时间戳）
 * @param endTime 结束时间（毫秒时间戳）
 */
export function filterGkpFilesByTime(
  gkpFiles: GkpFileInfo[],
  startTime?: number,
  endTime?: number
): GkpFileInfo[] {
  return gkpFiles.filter(file => {
    if (startTime && file.timestamp < startTime) return false;
    if (endTime && file.timestamp > endTime) return false;
    return true;
  });
}

/**
 * 获取最近N天的GKP文件
 * @param gkpFiles GKP文件列表
 * @param days 天数，默认7天
 */
export function getRecentGkpFiles(
  gkpFiles: GkpFileInfo[],
  days: number = 7
): GkpFileInfo[] {
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  return gkpFiles.filter(file => file.timestamp >= cutoff);
}

/**
 * 格式化导入建议显示
 */
export function formatSuggestionDisplay(suggestion: ImportSuggestion): {
  title: string;
  subtitle: string;
  income: string;
  expense: string;
  confidence: string;
} {
  const date = new Date(suggestion.timestamp);
  const dateStr = date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
  
  return {
    title: `${suggestion.playerCount}人${suggestion.difficulty ? suggestion.difficulty : ''}${suggestion.raidName}`,
    subtitle: dateStr,
    income: suggestion.goldIncome > 0 ? `+${suggestion.goldIncome.toLocaleString()}金` : '-',
    expense: suggestion.goldExpense > 0 ? `-${suggestion.goldExpense.toLocaleString()}金` : '-',
    confidence: `${Math.round(suggestion.confidence * 100)}%`,
  };
}

/**
 * 将导入建议转换为RaidRecord部分字段
 * 用于预填充AddRecordModal表单
 */
export function suggestionToRecordFields(suggestion: ImportSuggestion): {
  raidName: string;
  date: number;
  goldIncome: number;
  goldExpense: number;
  notes: string;
} {
  return {
    raidName: `${suggestion.playerCount}人${suggestion.difficulty ? suggestion.difficulty : ''}${suggestion.raidName}`,
    date: suggestion.timestamp,
    goldIncome: suggestion.goldIncome,
    goldExpense: suggestion.goldExpense,
    notes: `从游戏导入 (置信度: ${Math.round(suggestion.confidence * 100)}%)`,
  };
}
