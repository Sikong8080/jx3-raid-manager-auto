import React, { useState } from 'react';
import { X, Download, RefreshCw, AlertCircle } from 'lucide-react';
import { UpdateInfo, UpdateState } from '../types';
import { downloadAndInstall, DownloadProgress } from '../services/updater';

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  updateInfo: UpdateInfo;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({
  isOpen,
  onClose,
  updateInfo,
}) => {
  const [state, setState] = useState<UpdateState>('available');
  const [progress, setProgress] = useState<DownloadProgress>({ downloaded: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = async () => {
    setState('downloading');
    setError(null);

    try {
      await downloadAndInstall((p: DownloadProgress) => {
        setProgress(p);
      });
      // relaunch 会在 downloadAndInstall 内调用，此处不会执行到
    } catch (err) {
      console.error('更新失败:', err);
      setState('error');
      setError(err instanceof Error ? err.message : '更新过程中发生未知错误');
    }
  };

  const handleRetry = () => {
    setState('available');
    setError(null);
    setProgress({ downloaded: 0, total: 0 });
  };

  const progressPercent = progress.total > 0
    ? Math.min(Math.round((progress.downloaded / progress.total) * 100), 100)
    : 0;

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  if (!isOpen) return null;

  const isDownloading = state === 'downloading';
  const canClose = !isDownloading;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 z-40 transition-opacity duration-200"
        onClick={canClose ? onClose : undefined}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-surface border border-base rounded-xl shadow-xl w-full max-w-md overflow-hidden pointer-events-auto animate-in fade-in zoom-in-95 duration-200">
          {/* 标题栏 */}
          <div className="px-6 py-4 flex items-center justify-between border-b border-base">
            <div className="flex items-center gap-2">
              <Download className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <h2 className="text-lg font-semibold text-main">发现新版本</h2>
            </div>
            {canClose && (
              <button
                onClick={onClose}
                className="text-muted hover:text-main hover:bg-base p-1.5 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          <div className="p-6 space-y-5">
            {/* 版本信息 */}
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 text-sm font-medium rounded-full border border-emerald-200 dark:border-emerald-800">
                v{updateInfo.version}
              </span>
              {updateInfo.date && (
                <span className="text-sm text-muted">
                  {new Date(updateInfo.date).toLocaleDateString('zh-CN')}
                </span>
              )}
            </div>

            {/* 更新日志 */}
            {updateInfo.body && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-main">更新内容</h3>
                <div className="p-3 bg-base rounded-lg text-sm text-muted leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {updateInfo.body}
                </div>
              </div>
            )}

            {/* 下载进度 */}
            {isDownloading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted">正在下载更新...</span>
                  <span className="text-main font-medium">
                    {progress.total > 0
                      ? `${formatBytes(progress.downloaded)} / ${formatBytes(progress.total)}`
                      : formatBytes(progress.downloaded)
                    }
                  </span>
                </div>
                <div className="h-2 bg-base rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 dark:bg-emerald-400 rounded-full transition-all duration-300 ease-out"
                    style={{ width: progress.total > 0 ? `${progressPercent}%` : '100%' }}
                  />
                </div>
                {progress.total > 0 && (
                  <div className="text-right text-xs text-muted">{progressPercent}%</div>
                )}
              </div>
            )}

            {/* 错误提示 */}
            {state === 'error' && error && (
              <div className="p-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2 text-red-600 dark:text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">更新失败</p>
                  <p className="mt-1 text-red-500 dark:text-red-400/80">{error}</p>
                </div>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex gap-3 pt-2">
              {state === 'available' && (
                <>
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-4 py-2.5 border border-base text-main rounded-lg font-medium hover:bg-base transition-colors active:scale-[0.98]"
                  >
                    稍后提醒
                  </button>
                  <button
                    type="button"
                    onClick={handleUpdate}
                    className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium shadow-sm transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    立即更新
                  </button>
                </>
              )}

              {isDownloading && (
                <div className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg font-medium border border-emerald-200 dark:border-emerald-800">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  正在更新，请勿关闭...
                </div>
              )}

              {state === 'error' && (
                <>
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-4 py-2.5 border border-base text-main rounded-lg font-medium hover:bg-base transition-colors active:scale-[0.98]"
                  >
                    取消
                  </button>
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium shadow-sm transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    重试
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
