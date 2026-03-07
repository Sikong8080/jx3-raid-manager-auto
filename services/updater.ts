import { check, Update } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';
import { UpdateInfo } from '../types';

/** 当前缓存的 Update 对象（用于后续下载安装） */
let pendingUpdate: Update | null = null;

/**
 * 检查是否有新版本可用
 * @returns UpdateInfo 对象（有新版本时）或 null（已是最新）
 */
export async function checkForUpdates(): Promise<UpdateInfo | null> {
  try {
    const update = await check({ timeout: 30000 });

    if (update) {
      pendingUpdate = update;
      return {
        version: update.version,
        body: update.body ?? null,
        date: update.date ?? null,
      };
    }

    pendingUpdate = null;
    return null;
  } catch (error) {
    console.error('检查更新失败:', error);
    pendingUpdate = null;
    return null;
  }
}

/** 下载进度回调参数 */
export interface DownloadProgress {
  /** 已下载字节数 */
  downloaded: number;
  /** 总字节数（可能为 0，表示未知） */
  total: number;
}

/**
 * 下载并安装更新，完成后自动重启应用
 * @param onProgress 下载进度回调
 * @throws 如果没有待安装的更新或下载失败
 */
export async function downloadAndInstall(
  onProgress?: (progress: DownloadProgress) => void
): Promise<void> {
  if (!pendingUpdate) {
    throw new Error('没有可用的更新');
  }

  let downloaded = 0;
  let total = 0;

  await pendingUpdate.downloadAndInstall((event) => {
    switch (event.event) {
      case 'Started':
        total = event.data.contentLength ?? 0;
        downloaded = 0;
        onProgress?.({ downloaded: 0, total });
        break;
      case 'Progress':
        downloaded += event.data.chunkLength;
        onProgress?.({ downloaded, total });
        break;
      case 'Finished':
        onProgress?.({ downloaded: total || downloaded, total: total || downloaded });
        break;
    }
  });

  // 安装完成后重启应用
  await relaunch();
}
