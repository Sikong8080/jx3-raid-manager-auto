import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Raid, RaidRecord, Config, ImportSuggestion } from '../types';
import { X, AlertCircle, Users, Check, CheckSquare, Square, RefreshCw, TrendingUp, TrendingDown, FileText, Search } from 'lucide-react';
import { generateUUID } from '../utils/uuid';
import { scanGkpDirectory } from '../services/gkpDirectoryScanner';
import { matchGkpWithChatlog } from '../services/importMatcher';
import { getLastMonday, getNextMonday } from '../utils/cooldownManager';

interface RoleForBatchImport {
  id: string;
  name: string;
  server: string;
  region: string;
  sect: string;
  accountId: string;
  accountName: string;
  canAddMore: boolean;
  equipmentScore?: number;
}

interface RoleScanResult {
  roleId: string;
  roleName: string;
  server: string;
  accountName: string;
  status: 'pending' | 'scanning' | 'success' | 'error' | 'no_data';
  suggestion?: ImportSuggestion;
  error?: string;
}

interface BatchImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (records: Partial<RaidRecord>[]) => Promise<void>;
  raid: Raid;
  roles: RoleForBatchImport[];
  config?: Config;
}

type ModalStep = 'select' | 'scanning' | 'result';

export const BatchImportModal: React.FC<BatchImportModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  raid,
  roles,
  config,
}) => {
  const [step, setStep] = useState<ModalStep>('select');
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedBossIds, setSelectedBossIds] = useState<string[]>([]);
  const [scanResults, setScanResults] = useState<RoleScanResult[]>([]);
  const [selectedResultIds, setSelectedResultIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 可导入的角色（canAddMore 为 true 的）
  const importableRoles = useMemo(() => {
    return roles.filter(r => r.canAddMore);
  }, [roles]);

  // 可用的 BOSS 列表
  const availableBosses = useMemo(() => {
    return raid.bosses || [];
  }, [raid]);

  // 成功扫描到数据的角色
  const successResults = useMemo(() => {
    return scanResults.filter(r => r.status === 'success' && r.suggestion);
  }, [scanResults]);

  // 当前周期时间范围
  const periodRange = useMemo(() => {
    const now = new Date();
    return {
      start: getLastMonday(now).getTime(),
      end: getNextMonday(now).getTime(),
    };
  }, []);

  const gameDirectory = config?.game?.gameDirectory;

  // 初始化
  useEffect(() => {
    if (isOpen) {
      setStep('select');
      setSelectedRoleIds(importableRoles.map(r => r.id)); // 默认全选
      setSelectedBossIds(availableBosses.map(b => b.id));
      setScanResults([]);
      setSelectedResultIds([]);
      setIsSubmitting(false);
      setErrorMessage(null);
    }
  }, [isOpen, importableRoles, availableBosses]);

  // 扫描单个角色
  const scanRole = useCallback(async (role: RoleForBatchImport): Promise<RoleScanResult> => {
    if (!gameDirectory) {
      return {
        roleId: role.id,
        roleName: role.name,
        server: role.server,
        accountName: role.accountName,
        status: 'error',
        error: '未配置游戏目录',
      };
    }

    try {
      // 扫描 GKP 文件
      const gkpResult = await scanGkpDirectory({
        gameDirectory,
        activeRoles: [{ name: role.name, server: role.server, region: role.region }],
      });

      if (!gkpResult.success || gkpResult.files.length === 0) {
        return {
          roleId: role.id,
          roleName: role.name,
          server: role.server,
          accountName: role.accountName,
          status: 'no_data',
          error: '未找到 GKP 文件',
        };
      }

      // 过滤当前周期内的文件
      const periodFiles = gkpResult.files.filter(
        file => file.timestamp >= periodRange.start && file.timestamp < periodRange.end
      );
      if (periodFiles.length === 0) {
        return {
          roleId: role.id,
          roleName: role.name,
          server: role.server,
          accountName: role.accountName,
          status: 'no_data',
          error: '本周期无记录',
        };
      }

      // 按当前副本过滤
      const matchedFiles = periodFiles.filter(f => {
        if (f.playerCount !== raid.playerCount) return false;
        if (!f.mapName.includes(raid.name) && !raid.name.includes(f.mapName)) return false;
        const gkpDifficulty = f.difficulty || '普通';
        if (gkpDifficulty !== raid.difficulty) return false;
        return true;
      });

      if (matchedFiles.length === 0) {
        return {
          roleId: role.id,
          roleName: role.name,
          server: role.server,
          accountName: role.accountName,
          status: 'no_data',
          error: '无匹配副本记录',
        };
      }

      // 匹配聊天日志
      const matchResult = await matchGkpWithChatlog(matchedFiles, {
        gameDirectory,
        roleName: role.name,
        marginMinutes: 30,
        maxSuggestions: 1,
        minConfidence: 0.1,
      });

      if (matchResult.suggestions.length === 0) {
        return {
          roleId: role.id,
          roleName: role.name,
          server: role.server,
          accountName: role.accountName,
          status: 'no_data',
          error: '无有效金币记录',
        };
      }

      const bestSuggestion = matchResult.suggestions[0];

      return {
        roleId: role.id,
        roleName: role.name,
        server: role.server,
        accountName: role.accountName,
        status: 'success',
        suggestion: bestSuggestion,
      };
    } catch (error) {
      return {
        roleId: role.id,
        roleName: role.name,
        server: role.server,
        accountName: role.accountName,
        status: 'error',
        error: error instanceof Error ? error.message : '扫描失败',
      };
    }
  }, [gameDirectory, raid]);

  // 开始扫描选中的角色
  const startScan = useCallback(async () => {
    if (!gameDirectory) {
      setErrorMessage('请先在设置中配置游戏目录');
      return;
    }

    if (selectedRoleIds.length === 0) {
      setErrorMessage('请至少选择一个角色');
      return;
    }

    setStep('scanning');
    setErrorMessage(null);

    // 获取选中的角色
    const rolesToScan = importableRoles.filter(r => selectedRoleIds.includes(r.id));

    // 初始化扫描结果
    const initialResults: RoleScanResult[] = rolesToScan.map(role => ({
      roleId: role.id,
      roleName: role.name,
      server: role.server,
      accountName: role.accountName,
      status: 'pending',
    }));
    setScanResults(initialResults);

    // 逐个扫描角色
    const results: RoleScanResult[] = [];
    for (const role of rolesToScan) {
      // 更新当前角色状态为扫描中
      setScanResults(prev => prev.map(r => 
        r.roleId === role.id ? { ...r, status: 'scanning' } : r
      ));

      const result = await scanRole(role);
      results.push(result);

      // 更新扫描结果
      setScanResults(prev => prev.map(r => 
        r.roleId === role.id ? result : r
      ));
    }

    // 自动选中所有成功扫描到数据的角色
    const successIds = results.filter(r => r.status === 'success').map(r => r.roleId);
    setSelectedResultIds(successIds);
    
    setStep('result');
  }, [gameDirectory, selectedRoleIds, importableRoles, scanRole]);

  const constructRaidName = (): string => {
    return `${raid.playerCount}人${raid.difficulty}${raid.name}`;
  };

  const handleToggleRole = (roleId: string) => {
    setSelectedRoleIds(prev => 
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  const handleSelectAllRoles = () => {
    if (selectedRoleIds.length === importableRoles.length) {
      setSelectedRoleIds([]);
    } else {
      setSelectedRoleIds(importableRoles.map(r => r.id));
    }
  };

  const handleToggleResult = (roleId: string) => {
    const result = scanResults.find(r => r.roleId === roleId);
    if (result?.status !== 'success') return;
    
    setSelectedResultIds(prev => 
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  const handleSelectAllResults = () => {
    const selectableIds = successResults.map(r => r.roleId);
    if (selectedResultIds.length === selectableIds.length) {
      setSelectedResultIds([]);
    } else {
      setSelectedResultIds(selectableIds);
    }
  };

  const handleSubmit = async () => {
    if (selectedResultIds.length === 0) {
      setErrorMessage('请至少选择一个角色');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const records: Partial<RaidRecord>[] = selectedResultIds.map(roleId => {
        const result = scanResults.find(r => r.roleId === roleId);
        const role = importableRoles.find(r => r.id === roleId)!;
        const suggestion = result?.suggestion;

        return {
          id: generateUUID(),
          accountId: role.accountId,
          roleId: role.id,
          raidName: constructRaidName(),
          date: suggestion?.timestamp || Date.now(),
          goldIncome: suggestion?.goldIncome || 0,
          goldExpense: suggestion?.goldExpense || undefined,
          hasXuanjing: false,
          hasMaJu: false,
          hasPet: false,
          hasPendant: false,
          hasMount: false,
          hasAppearance: false,
          hasTitle: false,
          hasSecretBook: false,
          notes: `自动导入 (置信度: ${Math.round((suggestion?.confidence || 0) * 100)}%)`,
          roleName: role.name,
          server: `${role.region} ${role.server}`,
          transactionType: 'combined',
          bossIds: selectedBossIds.length > 0 ? selectedBossIds : undefined,
          bossNames: selectedBossIds.map(id => availableBosses.find(b => b.id === id)?.name).filter(Boolean) as string[] || undefined,
        };
      });

      await onSubmit(records);
      onClose();
    } catch (error) {
      console.error('批量导入失败:', error);
      setErrorMessage('批量导入失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBack = () => {
    setStep('select');
    setScanResults([]);
    setSelectedResultIds([]);
  };

  if (!isOpen) return null;

  // 统计
  const totalIncome = successResults
    .filter(r => selectedResultIds.includes(r.roleId))
    .reduce((sum, r) => sum + (r.suggestion?.goldIncome || 0), 0);
  const totalExpense = successResults
    .filter(r => selectedResultIds.includes(r.roleId))
    .reduce((sum, r) => sum + (r.suggestion?.goldExpense || 0), 0);

  return createPortal(
    <>
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100]"
        onClick={(e) => {
          if (e.target === e.currentTarget && step !== 'scanning') {
            onClose();
          }
        }}
      />
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-surface rounded-xl shadow-2xl w-full max-w-lg overflow-hidden pointer-events-auto transition-all duration-300 max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 border-b border-base flex items-center justify-between bg-surface/50 backdrop-blur-sm flex-shrink-0">
            <div>
              <h2 className="text-lg font-bold text-main flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" />
                批量导入
              </h2>
              <p className="text-muted text-xs mt-0.5">
                自动扫描游戏记录导入 <span className="font-medium text-main">{constructRaidName()}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              disabled={step === 'scanning'}
              className="text-muted hover:text-main transition-colors p-2 rounded-lg hover:bg-base/50 disabled:opacity-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-5 space-y-4 overflow-y-auto flex-1">
            {/* 步骤1: 选择角色 */}
            {step === 'select' && (
              <>
                {/* 无游戏目录配置 */}
                {!gameDirectory && (
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                    <p className="text-sm text-amber-700 dark:text-amber-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      请先在设置中配置游戏目录
                    </p>
                  </div>
                )}

                {/* BOSS 选择（如果有的话） */}
                {availableBosses.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-main mb-1.5">
                      击败BOSS（可多选）
                    </label>
                    <div className="grid grid-cols-3 gap-2 p-3 bg-base rounded-lg border border-base">
                      {availableBosses.map((boss) => {
                        const isSelected = selectedBossIds.includes(boss.id);
                        return (
                          <label
                            key={boss.id}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all ${isSelected
                              ? 'bg-primary text-white'
                              : 'bg-surface text-muted border border-base hover:border-primary hover:text-primary'
                              }`}
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedBossIds([...selectedBossIds, boss.id]);
                                } else {
                                  setSelectedBossIds(selectedBossIds.filter(id => id !== boss.id));
                                }
                              }}
                              className="sr-only"
                            />
                            <span className="text-sm font-medium">{boss.name}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 角色选择列表 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-main">
                      选择角色（{selectedRoleIds.length}/{importableRoles.length}）
                    </label>
                    {importableRoles.length > 0 && (
                      <button
                        type="button"
                        onClick={handleSelectAllRoles}
                        className="text-xs text-primary hover:text-primary-hover flex items-center gap-1"
                      >
                        {selectedRoleIds.length === importableRoles.length ? (
                          <>
                            <CheckSquare className="w-3.5 h-3.5" />
                            取消全选
                          </>
                        ) : (
                          <>
                            <Square className="w-3.5 h-3.5" />
                            全选
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {importableRoles.length === 0 ? (
                    <div className="p-4 bg-base rounded-lg border border-base text-center text-muted text-sm">
                      没有可以添加记录的角色（所有角色本周期都已有记录）
                    </div>
                  ) : (
                    <div className="max-h-64 overflow-y-auto border border-base rounded-lg divide-y divide-base">
                      {importableRoles.map(role => {
                        const isSelected = selectedRoleIds.includes(role.id);
                        return (
                          <label
                            key={role.id}
                            className={`flex items-center gap-3 p-3 cursor-pointer transition-colors ${
                              isSelected ? 'bg-primary/5' : 'hover:bg-base/50'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleRole(role.id)}
                              className="sr-only"
                            />
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                              isSelected 
                                ? 'bg-primary border-primary' 
                                : 'border-base'
                            }`}>
                              {isSelected && <Check className="w-3 h-3 text-white" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-main truncate">{role.name}</span>
                                <span className="text-xs text-muted">@{role.server}</span>
                                {role.sect && role.sect !== '未知' && (
                                  <span className="text-xs bg-base px-1.5 py-0.5 rounded text-muted">{role.sect}</span>
                                )}
                                {role.equipmentScore && (
                                  <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                                    {role.equipmentScore.toLocaleString()}
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-muted mt-0.5">{role.accountName}</div>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* 错误信息 */}
                {errorMessage && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      {errorMessage}
                    </p>
                  </div>
                )}

                {/* 按钮 */}
                <div className="flex gap-2.5 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-4 py-2.5 border border-base text-main rounded-lg font-medium hover:bg-base transition-colors text-sm"
                  >
                    取消
                  </button>
                  <button
                    onClick={startScan}
                    disabled={selectedRoleIds.length === 0 || !gameDirectory}
                    className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
                  >
                    <Search className="w-4 h-4" />
                    <span>扫描 ({selectedRoleIds.length})</span>
                  </button>
                </div>
              </>
            )}

            {/* 步骤2: 扫描中 */}
            {step === 'scanning' && (
              <div className="py-4">
                <div className="flex flex-col items-center justify-center mb-6">
                  <RefreshCw className="w-10 h-10 text-primary animate-spin mb-3" />
                  <p className="text-main font-medium">正在扫描游戏记录...</p>
                  <p className="text-muted text-sm mt-1">
                    已扫描 {scanResults.filter(r => r.status !== 'pending' && r.status !== 'scanning').length} / {scanResults.length} 个角色
                  </p>
                </div>

                {/* 扫描进度列表 */}
                <div className="max-h-48 overflow-y-auto border border-base rounded-lg divide-y divide-base">
                  {scanResults.map(result => (
                    <div key={result.roleId} className="flex items-center gap-3 p-3">
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-main">{result.roleName}</span>
                        <span className="text-xs text-muted ml-2">@{result.server}</span>
                      </div>
                      <div className="flex-shrink-0">
                        {result.status === 'scanning' && (
                          <RefreshCw className="w-4 h-4 text-primary animate-spin" />
                        )}
                        {result.status === 'pending' && (
                          <span className="text-xs text-muted">等待中</span>
                        )}
                        {result.status === 'success' && (
                          <Check className="w-4 h-4 text-emerald-500" />
                        )}
                        {(result.status === 'error' || result.status === 'no_data') && (
                          <span className="text-xs text-muted">{result.error}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 步骤3: 扫描结果 */}
            {step === 'result' && (
              <>
                {/* 结果列表 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-main">
                      扫描结果（{selectedResultIds.length}/{successResults.length} 已选）
                    </label>
                    {successResults.length > 0 && (
                      <button
                        type="button"
                        onClick={handleSelectAllResults}
                        className="text-xs text-primary hover:text-primary-hover flex items-center gap-1"
                      >
                        {selectedResultIds.length === successResults.length ? (
                          <>
                            <CheckSquare className="w-3.5 h-3.5" />
                            取消全选
                          </>
                        ) : (
                          <>
                            <Square className="w-3.5 h-3.5" />
                            全选
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  <div className="max-h-64 overflow-y-auto border border-base rounded-lg divide-y divide-base">
                    {scanResults.map(result => {
                      const isSelectable = result.status === 'success';
                      const isSelected = selectedResultIds.includes(result.roleId);
                      
                      return (
                        <div
                          key={result.roleId}
                          onClick={() => isSelectable && handleToggleResult(result.roleId)}
                          className={`flex items-center gap-3 p-3 transition-colors ${
                            isSelectable ? 'cursor-pointer' : 'cursor-default opacity-60'
                          } ${isSelected ? 'bg-primary/5' : isSelectable ? 'hover:bg-base/50' : ''}`}
                        >
                          {/* 复选框 */}
                          <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors flex-shrink-0 ${
                            isSelected 
                              ? 'bg-primary border-primary' 
                              : isSelectable
                                ? 'border-base'
                                : 'border-base/50 bg-base/30'
                          }`}>
                            {isSelected && <Check className="w-3 h-3 text-white" />}
                          </div>

                          {/* 角色信息 */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-main truncate">{result.roleName}</span>
                              <span className="text-xs text-muted">@{result.server}</span>
                            </div>
                            <div className="text-xs text-muted mt-0.5">{result.accountName}</div>
                          </div>

                          {/* 扫描结果 */}
                          <div className="flex-shrink-0 text-right">
                            {result.status === 'success' && result.suggestion && (
                              <div>
                                <div className="flex items-center gap-1 text-emerald-600 justify-end">
                                  <TrendingUp className="w-3 h-3" />
                                  <span className="text-xs font-mono">+{result.suggestion.goldIncome.toLocaleString()}</span>
                                </div>
                                {result.suggestion.goldExpense > 0 && (
                                  <div className="flex items-center gap-1 text-amber-600 justify-end mt-0.5">
                                    <TrendingDown className="w-3 h-3" />
                                    <span className="text-xs font-mono">-{result.suggestion.goldExpense.toLocaleString()}</span>
                                  </div>
                                )}
                              </div>
                            )}
                            {(result.status === 'error' || result.status === 'no_data') && (
                              <span className="text-xs text-muted">{result.error}</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 汇总统计 */}
                {selectedResultIds.length > 0 && (
                  <div className="p-3 bg-base rounded-lg flex items-center justify-between">
                    <span className="text-sm text-muted">
                      已选 <span className="font-medium text-main">{selectedResultIds.length}</span> 个角色
                    </span>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1 text-emerald-600">
                        <TrendingUp className="w-4 h-4" />
                        <span className="text-sm font-mono font-medium">+{totalIncome.toLocaleString()}</span>
                      </div>
                      {totalExpense > 0 && (
                        <div className="flex items-center gap-1 text-amber-600">
                          <TrendingDown className="w-4 h-4" />
                          <span className="text-sm font-mono font-medium">-{totalExpense.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 错误信息 */}
                {errorMessage && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      {errorMessage}
                    </p>
                  </div>
                )}

                {/* 按钮 */}
                <div className="flex gap-2.5 pt-2">
                  <button
                    type="button"
                    onClick={handleBack}
                    disabled={isSubmitting}
                    className="px-4 py-2.5 border border-base text-main rounded-lg font-medium hover:bg-base transition-colors text-sm"
                  >
                    返回
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2.5 border border-base text-main rounded-lg font-medium hover:bg-base transition-colors text-sm"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || selectedResultIds.length === 0}
                    className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                        <span>导入中...</span>
                      </>
                    ) : (
                      <>
                        <FileText className="w-4 h-4" />
                        <span>导入 ({selectedResultIds.length})</span>
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>,
    document.body
  );
};
