/**
 * 从游戏导入记录弹窗
 * 扫描GKP文件和聊天日志，展示分析结果供用户选择
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { X, Download, RefreshCw, AlertCircle, CheckCircle2, TrendingUp, TrendingDown, Clock, FileText, ChevronRight, Copy, Check } from 'lucide-react';
import { ImportSuggestion, Config, Raid } from '../types';
import { scanGkpDirectory } from '../services/gkpDirectoryScanner';
import { matchGkpWithChatlog, formatSuggestionDisplay } from '../services/importMatcher';
import { getLastMonday, getNextMonday } from '../utils/cooldownManager';

interface RoleInfo {
  id: string;
  name: string;
  server: string;
  region: string;
}

interface ImportFromGameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (suggestion: ImportSuggestion) => void;
  config: Config;
  role: RoleInfo;
  raid: Raid;  // 当前选择的副本（用于过滤匹配结果）
}

type ScanStatus = 'idle' | 'scanning' | 'done' | 'error';

export const ImportFromGameModal: React.FC<ImportFromGameModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  config,
  role,
  raid,
}) => {
  const [status, setStatus] = useState<ScanStatus>('idle');
  const [suggestions, setSuggestions] = useState<ImportSuggestion[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);  // 展开明细的ID
  const [copiedId, setCopiedId] = useState<string | null>(null);      // 已复制的ID（用于反馈）
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [scanLogs, setScanLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);

  const gameDirectory = config.game.gameDirectory;

  // 当前周期时间范围
  const periodRange = useMemo(() => {
    const now = new Date();
    return {
      start: getLastMonday(now).getTime(),
      end: getNextMonday(now).getTime(),
    };
  }, []);

  // 执行扫描
  const performScan = useCallback(async () => {
    if (!gameDirectory) {
      setErrorMessage('请先在设置中配置游戏目录');
      setStatus('error');
      return;
    }

    setStatus('scanning');
    setErrorMessage(null);
    setSuggestions([]);
    setSelectedId(null);
    setScanLogs([]);

    const logs: string[] = [];
    const addLog = (msg: string) => {
      logs.push(msg);
      setScanLogs([...logs]);
    };

    try {
      addLog(`[配置] 游戏目录: ${gameDirectory}`);
      addLog(`[配置] 角色: ${role.name} @ ${role.region} ${role.server}`);
      
      // 1. 扫描GKP文件
      addLog(`[GKP] 开始扫描GKP文件...`);
      const gkpResult = await scanGkpDirectory({
        gameDirectory,
        activeRoles: [{ name: role.name, server: role.server, region: role.region }],
      });

      addLog(`[GKP] 扫描结果: success=${gkpResult.success}, 文件数=${gkpResult.files.length}`);
      
      if (!gkpResult.success) {
        addLog(`[GKP] 扫描失败: ${gkpResult.error || '未知错误'}`);
        setErrorMessage('扫描GKP文件失败，请确认游戏目录配置正确');
        setStatus('error');
        return;
      }
      
      if (gkpResult.files.length === 0) {
        addLog(`[GKP] 未找到任何GKP文件`);
        addLog(`[GKP] 预期路径: ${gameDirectory}\\Game\\JX3\\bin\\zhcn_hd\\interface\\GKP\\`);
        setErrorMessage('未找到GKP文件，请确认游戏目录配置正确');
        setStatus('error');
        return;
      }

      // 打印找到的文件
      gkpResult.files.slice(0, 5).forEach((f, i) => {
        addLog(`[GKP] 文件${i + 1}: ${f.fileName} (${new Date(f.timestamp).toLocaleString()})`);
      });
      if (gkpResult.files.length > 5) {
        addLog(`[GKP] ... 还有 ${gkpResult.files.length - 5} 个文件`);
      }

      // 只处理当前周期内的文件
      const periodFiles = gkpResult.files.filter(
        file => file.timestamp >= periodRange.start && file.timestamp < periodRange.end
      );
      const periodStartStr = new Date(periodRange.start).toLocaleString();
      const periodEndStr = new Date(periodRange.end).toLocaleString();
      addLog(`[GKP] 当前周期: ${periodStartStr} ~ ${periodEndStr}`);
      addLog(`[GKP] 本周期内的文件: ${periodFiles.length} 个`);
      
      if (periodFiles.length === 0) {
        addLog(`[GKP] 本周期内没有副本记录`);
        setErrorMessage('本周期内没有副本记录');
        setStatus('error');
        return;
      }

      // 按当前副本过滤GKP文件（名称+人数+难度）
      const raidFullName = `${raid.playerCount}人${raid.difficulty}${raid.name}`;
      const matchedFiles = periodFiles.filter(f => {
        // 人数必须匹配
        if (f.playerCount !== raid.playerCount) return false;
        // 副本名称必须匹配（GKP的mapName应与raid.name一致）
        if (!f.mapName.includes(raid.name) && !raid.name.includes(f.mapName)) return false;
        // 难度匹配：GKP无难度标记视为"普通"
        const gkpDifficulty = f.difficulty || '普通';
        if (gkpDifficulty !== raid.difficulty) return false;
        return true;
      });
      addLog(`[GKP] 匹配当前副本 [${raidFullName}] 的文件: ${matchedFiles.length} 个`);

      if (matchedFiles.length === 0) {
        addLog(`[GKP] 本周期内没有匹配 [${raidFullName}] 的记录`);
        addLog(`[提示] 可用文件: ${periodFiles.map(f => `${f.playerCount}人${f.difficulty || ''}${f.mapName}`).join(', ')}`);
        setErrorMessage(`本周期内没有 [${raidFullName}] 的GKP记录`);
        setStatus('error');
        return;
      }

      // 2. 匹配聊天日志
      addLog(`[聊天日志] 开始匹配聊天日志...`);
      const matchResult = await matchGkpWithChatlog(matchedFiles, {
        gameDirectory,
        roleName: role.name,
        maxSuggestions: 10,
        minConfidence: 0.1,
        // 传入所有本周期的GKP文件用于计算时间边界，避免连续副本记录重叠
        allGkpFilesForBoundary: periodFiles,
      });

      // 合并匹配器返回的日志
      if (matchResult.scanLogs) {
        matchResult.scanLogs.forEach(log => addLog(log));
      }

      addLog(`[结果] 生成建议数: ${matchResult.suggestions.length}`);

      if (matchResult.suggestions.length === 0) {
        addLog(`[结果] 未能匹配到有效记录`);
        addLog(`[提示] 可能原因: 1) chatlog.db路径不匹配 2) 聊天记录时间范围不符 3) 没有金币相关记录`);
        setErrorMessage('未能匹配到有效的副本记录');
        setStatus('error');
        setShowLogs(true); // 错误时自动展开日志
        return;
      }

      setSuggestions(matchResult.suggestions);
      setStatus('done');
    } catch (error) {
      console.error('扫描失败:', error);
      addLog(`[错误] ${error instanceof Error ? error.message : String(error)}`);
      setErrorMessage(`扫描失败: ${error instanceof Error ? error.message : String(error)}`);
      setStatus('error');
      setShowLogs(true); // 错误时自动展开日志
    }
  }, [gameDirectory, role, raid]);

  // 打开时自动扫描
  useEffect(() => {
    if (isOpen && status === 'idle') {
      performScan();
    }
  }, [isOpen, status, performScan]);

  // 关闭时重置状态
  useEffect(() => {
    if (!isOpen) {
      setStatus('idle');
      setSuggestions([]);
      setSelectedId(null);
      setErrorMessage(null);
      setScanLogs([]);
      setShowLogs(false);
    }
  }, [isOpen]);

  const handleConfirm = () => {
    const selected = suggestions.find(s => s.id === selectedId);
    if (selected) {
      onSelect(selected);
      onClose();
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <>
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[110]"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
      />
      <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-surface rounded-xl shadow-2xl w-full max-w-lg overflow-hidden pointer-events-auto">
          {/* 标题栏 */}
          <div className="px-6 py-4 border-b border-base flex items-center justify-between bg-surface/50">
            <div>
              <h2 className="text-lg font-bold text-main flex items-center gap-2">
                <Download className="w-5 h-5 text-primary" />
                从游戏导入记录
              </h2>
              <p className="text-muted text-xs mt-0.5">
                <span className="font-medium text-main">{role.name}</span>
                <span className="mx-1.5 text-muted/40">·</span>
                {role.region} {role.server}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-muted hover:text-main transition-colors p-2 rounded-lg hover:bg-base/50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* 内容区 */}
          <div className="p-5">
            {/* 扫描中状态 */}
            {status === 'scanning' && (
              <div className="flex flex-col items-center justify-center py-12">
                <RefreshCw className="w-10 h-10 text-primary animate-spin mb-4" />
                <p className="text-main font-medium">正在扫描游戏数据...</p>
                <p className="text-muted text-sm mt-1">正在分析GKP文件和聊天日志</p>
              </div>
            )}

            {/* 错误状态 */}
            {status === 'error' && (
              <div className="py-4">
                <div className="flex flex-col items-center justify-center mb-4">
                  <AlertCircle className="w-12 h-12 text-amber-500 mb-3" />
                  <p className="text-main font-medium text-center">{errorMessage}</p>
                </div>
                
                {/* 调试日志区域 - 错误时始终显示 */}
                {scanLogs.length > 0 && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-muted">扫描日志</span>
                      <button
                        onClick={() => setShowLogs(!showLogs)}
                        className="text-xs text-primary hover:underline"
                      >
                        {showLogs ? '收起' : '展开'}
                      </button>
                    </div>
                    {showLogs && (
                      <div className="p-3 bg-slate-900 rounded-lg border border-slate-700 max-h-64 overflow-y-auto">
                        <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                          {scanLogs.join('\n')}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex justify-center gap-3">
                  <button
                    onClick={performScan}
                    className="btn btn-secondary flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    重新扫描
                  </button>
                  <button
                    onClick={onClose}
                    className="btn btn-ghost"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}

            {/* 扫描结果 */}
            {status === 'done' && (
              <>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-muted">
                    找到 <span className="text-main font-medium">{suggestions.length}</span> 条可能的副本记录
                  </p>
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="text-xs text-muted hover:text-primary transition-colors"
                  >
                    {showLogs ? '隐藏日志' : '查看扫描日志'}
                  </button>
                </div>

                {/* 扫描日志（可折叠） */}
                {showLogs && scanLogs.length > 0 && (
                  <div className="mb-4 p-3 bg-base rounded-lg border border-base max-h-32 overflow-y-auto">
                    <pre className="text-xs text-muted whitespace-pre-wrap font-mono">
                      {scanLogs.join('\n')}
                    </pre>
                  </div>
                )}

                {/* 建议列表 */}
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {suggestions.map((suggestion) => {
                    const display = formatSuggestionDisplay(suggestion);
                    const isSelected = selectedId === suggestion.id;
                    const isExpanded = expandedId === suggestion.id;
                    
                    return (
                      <div
                        key={suggestion.id}
                        className={`rounded-lg border-2 transition-all ${
                          isSelected
                            ? 'border-primary bg-primary/5'
                            : 'border-base hover:border-primary/50 bg-base/50'
                        }`}
                      >
                        {/* 主要信息区域 */}
                        <div
                          onClick={() => setSelectedId(suggestion.id)}
                          className="p-4 cursor-pointer"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                {isSelected && (
                                  <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0" />
                                )}
                                <h4 className="font-medium text-main">{display.title}</h4>
                              </div>
                              <div className="flex items-center gap-3 mt-1.5 text-sm text-muted">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5" />
                                  {display.subtitle}
                                </span>
                                <span className="flex items-center gap-1">
                                  <FileText className="w-3.5 h-3.5" />
                                  {suggestion.matchedChatCount}条记录
                                </span>
                              </div>
                            </div>
                            <div className="text-right flex-shrink-0 ml-4">
                              <div className="flex items-center gap-1 text-emerald-600">
                                <TrendingUp className="w-3.5 h-3.5" />
                                <span className="font-mono text-sm">{display.income}</span>
                              </div>
                              {suggestion.goldExpense > 0 && (
                                <div className="flex items-center gap-1 text-amber-600 mt-0.5">
                                  <TrendingDown className="w-3.5 h-3.5" />
                                  <span className="font-mono text-sm">{display.expense}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* 置信度指示器和查看明细按钮 */}
                          <div className="mt-3 flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-base rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${
                                  suggestion.confidence >= 0.7
                                    ? 'bg-emerald-500'
                                    : suggestion.confidence >= 0.4
                                    ? 'bg-amber-500'
                                    : 'bg-red-400'
                                }`}
                                style={{ width: `${suggestion.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted w-10 text-right">
                              {display.confidence}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setExpandedId(isExpanded ? null : suggestion.id);
                              }}
                              className="text-xs text-primary hover:underline ml-2"
                            >
                              {isExpanded ? '收起明细' : '查看明细'}
                            </button>
                          </div>
                        </div>
                        
                        {/* 展开的明细区域 */}
                        {isExpanded && (
                          <div className="px-4 pb-4 border-t border-base/50">
                            <div className="mt-3">
                              <div className="flex items-center justify-between mb-2">
                                <h5 className="text-xs font-medium text-muted">
                                  金币相关聊天记录 ({suggestion.chatRecords.length}条)
                                </h5>
                                {suggestion.chatRecords.length > 0 && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const text = suggestion.chatRecords
                                        .map(r => `${new Date(r.time * 1000).toLocaleTimeString()} ${r.text || r.msg}`)
                                        .join('\n');
                                      navigator.clipboard.writeText(text).then(() => {
                                        setCopiedId(suggestion.id);
                                        setTimeout(() => setCopiedId(null), 2000);
                                      });
                                    }}
                                    className="flex items-center gap-1 text-xs text-muted hover:text-primary transition-colors"
                                  >
                                    {copiedId === suggestion.id ? (
                                      <>
                                        <Check className="w-3 h-3 text-emerald-500" />
                                        <span className="text-emerald-500">已复制</span>
                                      </>
                                    ) : (
                                      <>
                                        <Copy className="w-3 h-3" />
                                        <span>复制明细</span>
                                      </>
                                    )}
                                  </button>
                                )}
                              </div>
                              <div className="max-h-48 overflow-y-auto space-y-1 bg-slate-900 rounded-lg p-2">
                                {suggestion.chatRecords.length === 0 ? (
                                  <p className="text-xs text-slate-400 text-center py-2">无金币相关记录</p>
                                ) : (
                                  suggestion.chatRecords.map((record, idx) => (
                                    <div key={idx} className="text-xs font-mono p-1.5 rounded bg-slate-800/50">
                                      <div className="text-slate-500 mb-0.5">
                                        {new Date(record.time * 1000).toLocaleTimeString()}
                                      </div>
                                      <div className="text-slate-300 break-all">
                                        {record.text || record.msg}
                                      </div>
                                    </div>
                                  ))
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* 底部操作栏 */}
          {status === 'done' && (
            <div className="px-6 py-4 border-t border-base bg-base/30 flex items-center justify-between">
              <button
                onClick={performScan}
                className="btn btn-ghost flex items-center gap-2 text-sm"
              >
                <RefreshCw className="w-4 h-4" />
                重新扫描
              </button>
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="btn btn-secondary"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={!selectedId}
                  className="btn btn-primary flex items-center gap-2"
                >
                  使用此记录
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>,
    document.body
  );
};
