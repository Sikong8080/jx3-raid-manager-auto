/**
 * 聊天日志扫描服务
 * 封装Tauri IPC调用，提供前端友好的API
 */

import { invoke } from '@tauri-apps/api/core';
import {
  ChatlogRecord,
  ChatlogScanRequest,
  ChatlogScanResult,
  FindChatlogPathResult,
} from '../types';

/**
 * 查找角色对应的chatlog.db路径
 */
export async function findChatlogPath(
  gameDirectory: string,
  roleName: string
): Promise<FindChatlogPathResult> {
  try {
    const resultJson = await invoke<string>('find_chatlog_path', {
      gameDirectory,
      roleName,
    });
    return JSON.parse(resultJson) as FindChatlogPathResult;
  } catch (error) {
    console.error('查找聊天日志路径失败:', error);
    return {
      success: false,
      error: `查找失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

/**
 * 扫描指定角色的聊天日志
 * @param request 扫描请求参数
 * @returns 扫描结果，包含聊天记录列表
 */
export async function scanChatlogForRole(
  request: ChatlogScanRequest
): Promise<ChatlogScanResult> {
  try {
    // 转换请求参数为Rust端期望的格式
    const rustRequest = {
      game_directory: request.gameDirectory,
      role_name: request.roleName,
      time_start: request.timeStart,
      time_end: request.timeEnd,
    };
    
    const resultJson = await invoke<string>('scan_chatlog_for_role', {
      request: JSON.stringify(rustRequest),
    });
    
    const result = JSON.parse(resultJson) as {
      success: boolean;
      records: ChatlogRecord[];
      chatlog_path?: string;
      error?: string;
      debug_info?: string[];
    };
    
    return {
      success: result.success,
      records: result.records,
      chatlogPath: result.chatlog_path,
      error: result.error,
      debugInfo: result.debug_info,
    };
  } catch (error) {
    console.error('扫描聊天日志失败:', error);
    return {
      success: false,
      records: [],
      error: `扫描失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

/**
 * 列出所有可用的聊天日志文件
 * @param gameDirectory 游戏目录
 * @returns chatlog.db路径列表
 */
export async function listAvailableChatlogs(
  gameDirectory: string
): Promise<string[]> {
  try {
    const resultJson = await invoke<string>('list_available_chatlogs', {
      gameDirectory,
    });
    return JSON.parse(resultJson) as string[];
  } catch (error) {
    console.error('列出聊天日志失败:', error);
    return [];
  }
}

/**
 * 直接从指定路径读取聊天日志
 * @param chatlogPath chatlog.db文件路径
 * @param timeStart 开始时间戳
 * @param timeEnd 结束时间戳
 * @returns 聊天记录列表
 */
export async function readChatlogFromPath(
  chatlogPath: string,
  timeStart: number,
  timeEnd: number
): Promise<ChatlogRecord[]> {
  try {
    const resultJson = await invoke<string>('read_chatlog_from_path', {
      chatlogPath,
      timeStart,
      timeEnd,
    });
    return JSON.parse(resultJson) as ChatlogRecord[];
  } catch (error) {
    console.error('读取聊天日志失败:', error);
    return [];
  }
}

/**
 * 扩展时间范围
 * 将GKP文件时间戳扩展为聊天日志查询范围
 * @param gkpStartTime GKP文件开始时间（秒）
 * @param gkpEndTime GKP文件结束时间（秒）
 * @param marginMinutes 扩展分钟数，默认30分钟
 * @returns [startTime, endTime] 扩展后的时间范围（秒）
 */
export function expandTimeRange(
  gkpStartTime: number,
  gkpEndTime?: number,
  marginMinutes: number = 30
): [number, number] {
  const marginSeconds = marginMinutes * 60;
  
  // 开始时间向前扩展
  const start = gkpStartTime - marginSeconds;
  
  // 结束时间向后扩展（如果没有结束时间，使用开始时间+2小时）
  const end = (gkpEndTime ?? gkpStartTime + 2 * 3600) + marginSeconds;
  
  return [start, end];
}

/**
 * 将毫秒时间戳转换为秒时间戳
 * GKP文件时间戳是毫秒，而chatlog.db的时间戳是秒
 */
export function msToSeconds(ms: number): number {
  return Math.floor(ms / 1000);
}

/**
 * 将秒时间戳转换为毫秒时间戳
 */
export function secondsToMs(seconds: number): number {
  return seconds * 1000;
}
