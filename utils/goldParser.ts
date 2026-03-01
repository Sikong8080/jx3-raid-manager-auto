/**
 * 金币解析工具
 * 用于从聊天记录文本中提取金币数量
 * 
 * 收入：从 msg 字段解析 "你获得：" 结构化数据（Text_Gold/Text_GoldB）
 * 支出：从 text 字段匹配角色购买和追加记录
 */

import { GoldParseResult } from '../types';

// 金砖正则：1金砖 = 10000金
const GOLD_BRICK_PATTERN = /(\d+)\s*金砖/g;

// 普通金币正则：匹配"X金"但不匹配"X金砖"
const GOLD_COIN_PATTERN = /(\d+)\s*金(?!砖)/g;

// 应该忽略的记录（叫价过程，不是最终成交）
const IGNORE_PATTERNS = [
  '叫价',      // 拍卖叫价过程
  '出价',      // 出价过程
  '当前价',    // 当前价格提示
  '记录给了',  // 团长分配记录，不是自己的支出
];

// 支出关键词（最终成交）
const EXPENSE_KEYWORDS = [
  '花费',          // [玩家]花费[金额]购买了[物品]
  '购买了',        // 最终成交
  '向团队里追加了', // 罚款/追加金币
];

// 收入关键词（仅用于向后兼容的文本分类，不再作为主要收入检测）
// 主要收入检测已改为从 msg 字段解析 Text_Gold/Text_GoldB
const INCOME_KEYWORDS = [
  '你获得：',
  '获得',
  '分配',
];

// 个人收入消息模式（msg字段中的XML结构）
const PERSONAL_INCOME_MSG_PATTERN = /text="(\d+)"[^>]*name="Text_(GoldB|Gold|Silver|Copper)"/g;

/**
 * 从文本中解析金币数量
 * 支持格式：
 * - "10金砖5金" → 100005
 * - "1234金" → 1234
 * - "5金砖" → 50000
 * - "获得10金砖2345金" → 102345
 */
export function parseGoldAmount(text: string): number {
  let total = 0;
  
  // 提取金砖 (1金砖 = 10000金)
  // 重置正则状态
  GOLD_BRICK_PATTERN.lastIndex = 0;
  const brickMatches = text.matchAll(new RegExp(GOLD_BRICK_PATTERN.source, 'g'));
  for (const match of brickMatches) {
    total += parseInt(match[1], 10) * 10000;
  }
  
  // 提取普通金币
  GOLD_COIN_PATTERN.lastIndex = 0;
  const coinMatches = text.matchAll(new RegExp(GOLD_COIN_PATTERN.source, 'g'));
  for (const match of coinMatches) {
    total += parseInt(match[1], 10);
  }
  
  return total;
}

/**
 * 判断文本是否包含金币信息
 */
export function hasGoldInfo(text: string): boolean {
  // 使用新的正则实例避免状态问题
  return /(\d+)\s*金砖/.test(text) || /(\d+)\s*金(?!砖)/.test(text);
}

/**
 * 从msg字段解析个人收入金额
 * 聊天记录的msg字段包含XML格式的金币数据，如：
 *   text="0" name="Text_GoldB"    → 金砖
 *   text="1304" name="Text_Gold"  → 金
 *   text="0" name="Text_Silver"   → 银
 *   text="0" name="Text_Copper"   → 铜
 * 
 * @returns 金额（单位：金），0表示无收入数据
 */
export function parsePersonalIncomeFromMsg(msg: string): number {
  if (!msg || !msg.includes('你获得')) return 0;
  if (!msg.includes('Text_Gold') && !msg.includes('Text_GoldB')) return 0;

  const cleanedMsg = msg.replace(/\s+/g, '');
  const matches = cleanedMsg.matchAll(
    new RegExp(PERSONAL_INCOME_MSG_PATTERN.source, 'g')
  );

  let goldBricks = 0;
  let gold = 0;
  let silver = 0;
  let copper = 0;

  for (const match of matches) {
    const value = parseInt(match[1], 10);
    const coinType = match[2];
    switch (coinType) {
      case 'GoldB': goldBricks = value; break;
      case 'Gold': gold = value; break;
      case 'Silver': silver = value; break;
      case 'Copper': copper = value; break;
    }
  }

  // 换算为"金"单位 (1金砖=10000金, 1金=1金, 100银=1金, 10000铜=1金)
  const totalCopper = (goldBricks * 10000 * 10000) + (gold * 10000) + (silver * 100) + copper;
  return Math.round(totalCopper / 10000);
}

/**
 * 判断记录是否应该被忽略（如叫价过程）
 */
export function shouldIgnoreRecord(text: string): boolean {
  return IGNORE_PATTERNS.some(pattern => text.includes(pattern));
}

/**
 * 分类交易类型（收入/支出）并解析金额
 * 只统计最终成交记录，忽略叫价过程
 */
export function classifyTransaction(text: string): GoldParseResult {
  // 先检查是否应该忽略（叫价等过程记录）
  if (shouldIgnoreRecord(text)) {
    return { type: 'unknown', amount: 0, raw: text };
  }
  
  const amount = parseGoldAmount(text);
  
  if (amount === 0) {
    return { type: 'unknown', amount: 0, raw: text };
  }
  
  // 检查收入关键词
  const hasIncome = INCOME_KEYWORDS.some(kw => text.includes(kw));
  
  // 检查支出关键词（必须是最终成交）
  const hasExpense = EXPENSE_KEYWORDS.some(kw => text.includes(kw));
  
  // 收入判定
  if (hasIncome) {
    return { type: 'income', amount, raw: text };
  }
  
  // 支出判定（只有最终成交才算）
  if (hasExpense) {
    return { type: 'expense', amount, raw: text };
  }
  
  // 无法确定类型（可能是叫价等中间过程）
  return { type: 'unknown', amount, raw: text };
}

/**
 * 分类交易类型，并过滤只统计指定角色的支出
 * @param text 聊天记录文本
 * @param currentRole 当前角色名（用于过滤支出）
 */
export function classifyTransactionForRole(text: string, currentRole?: string): GoldParseResult {
  // 先检查是否应该忽略（叫价等过程记录）
  if (shouldIgnoreRecord(text)) {
    return { type: 'unknown', amount: 0, raw: text };
  }
  
  const amount = parseGoldAmount(text);
  
  if (amount === 0) {
    return { type: 'unknown', amount: 0, raw: text };
  }
  
  // 检查收入关键词
  const hasIncome = INCOME_KEYWORDS.some(kw => text.includes(kw));
  
  // 收入判定
  if (hasIncome) {
    return { type: 'income', amount, raw: text };
  }
  
  // 检查支出（只有当前角色的花费才统计）
  if (EXPENSE_KEYWORDS.some(kw => text.includes(kw))) {
    // 如果指定了角色名，检查是否是该角色的支出
    if (currentRole) {
      // 匹配格式: [角色名]花费... 或 [角色名·服务器]花费...
      const rolePattern = new RegExp(`\\[${escapeRegex(currentRole)}[^\\]]*\\].*花费`);
      if (rolePattern.test(text)) {
        return { type: 'expense', amount, raw: text };
      }
      // 不是当前角色的支出，忽略
      return { type: 'unknown', amount: 0, raw: text };
    }
    return { type: 'expense', amount, raw: text };
  }
  
  // 无法确定类型
  return { type: 'unknown', amount, raw: text };
}

/**
 * 转义正则特殊字符
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * 判断聊天记录是否与当前角色相关且是有效的金币记录
 * 只包含：个人收入记录（msg字段）、购买记录、追加金币记录
 * @param text 聊天记录text字段
 * @param roleName 当前角色名
 * @param msg 聊天记录msg字段（用于检测个人收入）
 */
export function isRecordRelatedToRole(text: string, roleName: string, msg?: string): boolean {
  // 1. 个人收入：msg字段包含"你获得"且有Text_Gold结构化数据
  if (msg && msg.includes('你获得') && (msg.includes('Text_Gold') || msg.includes('Text_GoldB'))) {
    return true;
  }
  
  // 先排除叫价等无效记录
  if (IGNORE_PATTERNS.some(p => text.includes(p))) {
    return false;
  }
  
  const escapedRole = escapeRegex(roleName);
  // 匹配 [角色名] 或 [角色名·服务器]
  const rolePattern = new RegExp(`\\[${escapedRole}[^\\]]*\\]`);
  
  // 2. 当前角色的购买记录: [角色名]花费...购买了...
  if (rolePattern.test(text) && text.includes('花费') && text.includes('购买了')) {
    return true;
  }
  
  // 3. 当前角色的追加金币记录: [角色名]...向团队里追加了...
  if (rolePattern.test(text) && text.includes('向团队里追加了')) {
    return true;
  }
  
  return false;
}

/**
 * 聊天记录简化接口（避免循环引入）
 */
interface RecordLike {
  text: string;
  msg: string;
}

/**
 * 批量解析聊天记录中的金币信息
 * - 收入：从 msg 字段解析 "你获得" 结构化数据（准确的个人收入）
 * - 支出：从 text 字段匹配角色购买和追加记录
 * @param records 聊天记录数组
 * @param currentRole 当前角色名（用于过滤支出）
 */
export function aggregateGoldFromRecords(records: RecordLike[], currentRole?: string): {
  totalIncome: number;
  totalExpense: number;
  incomeRecords: GoldParseResult[];
  expenseRecords: GoldParseResult[];
  unknownRecords: GoldParseResult[];
} {
  const incomeRecords: GoldParseResult[] = [];
  const expenseRecords: GoldParseResult[] = [];
  const unknownRecords: GoldParseResult[] = [];
  
  let totalIncome = 0;
  let totalExpense = 0;
  
  for (const record of records) {
    // 1. 从 msg 字段检测个人收入
    const personalIncome = parsePersonalIncomeFromMsg(record.msg);
    if (personalIncome > 0) {
      const result: GoldParseResult = {
        type: 'income',
        amount: personalIncome,
        raw: record.text || record.msg,
      };
      incomeRecords.push(result);
      totalIncome += personalIncome;
      continue;
    }
    
    // 2. 从 text 字段检测支出（购买、追加金币）
    // 注意：只用 record.text，不拼接 record.msg，否则金额会被重复计算
    const result = currentRole
      ? classifyTransactionForRole(record.text, currentRole)
      : classifyTransaction(record.text);
    
    if (result.amount > 0 && result.type === 'expense') {
      expenseRecords.push(result);
      totalExpense += result.amount;
    } else if (result.amount > 0 && result.type !== 'income') {
      // 忽略 text 中的"income"分类（不准确，会计入团队总收入）
      unknownRecords.push(result);
    }
  }
  
  return {
    totalIncome,
    totalExpense,
    incomeRecords,
    expenseRecords,
    unknownRecords,
  };
}

/**
 * @deprecated 使用 aggregateGoldFromRecords 代替
 * 保留用于向后兼容
 */
export function aggregateGoldFromTexts(texts: string[], currentRole?: string): {
  totalIncome: number;
  totalExpense: number;
  incomeRecords: GoldParseResult[];
  expenseRecords: GoldParseResult[];
  unknownRecords: GoldParseResult[];
} {
  const incomeRecords: GoldParseResult[] = [];
  const expenseRecords: GoldParseResult[] = [];
  const unknownRecords: GoldParseResult[] = [];
  
  let totalIncome = 0;
  let totalExpense = 0;
  
  for (const text of texts) {
    const result = currentRole 
      ? classifyTransactionForRole(text, currentRole)
      : classifyTransaction(text);
    
    if (result.amount > 0) {
      switch (result.type) {
        case 'income':
          incomeRecords.push(result);
          totalIncome += result.amount;
          break;
        case 'expense':
          expenseRecords.push(result);
          totalExpense += result.amount;
          break;
        default:
          unknownRecords.push(result);
      }
    }
  }
  
  return {
    totalIncome,
    totalExpense,
    incomeRecords,
    expenseRecords,
    unknownRecords,
  };
}

/**
 * 格式化金币显示
 * 例如：152345 → "15金砖2345金" 或 "152,345金"
 */
export function formatGold(amount: number, useBrick: boolean = false): string {
  if (useBrick && amount >= 10000) {
    const bricks = Math.floor(amount / 10000);
    const remainder = amount % 10000;
    if (remainder > 0) {
      return `${bricks}金砖${remainder.toLocaleString()}金`;
    }
    return `${bricks}金砖`;
  }
  return `${amount.toLocaleString()}金`;
}

/**
 * 解析GKP分配消息
 * GKP格式通常为：[角色名] 分配 [金额]
 */
export function parseGkpDistribution(text: string): {
  roleName?: string;
  amount: number;
} | null {
  // 匹配 "[角色名] 分配 X金砖Y金" 格式
  const gkpPattern = /\[([^\]]+)\]\s*分配\s*(.+)/;
  const match = text.match(gkpPattern);
  
  if (match) {
    const roleName = match[1];
    const goldText = match[2];
    const amount = parseGoldAmount(goldText);
    
    return { roleName, amount };
  }
  
  return null;
}

/**
 * 计算置信度分数
 * 基于匹配的记录数量和金币识别成功率
 */
export function calculateConfidence(
  matchedChatCount: number,
  incomeRecordCount: number,
  totalGold: number
): number {
  // 基础分数：有匹配记录得0.3分
  let score = matchedChatCount > 0 ? 0.3 : 0;
  
  // 有收入记录得0.3分
  if (incomeRecordCount > 0) {
    score += 0.3;
  }
  
  // 金额合理性（假设正常副本收入在1000-500000之间）
  if (totalGold >= 1000 && totalGold <= 500000) {
    score += 0.2;
  } else if (totalGold > 0) {
    score += 0.1;
  }
  
  // 记录数量合理性（正常副本聊天记录在5-100条之间）
  if (matchedChatCount >= 5 && matchedChatCount <= 100) {
    score += 0.2;
  } else if (matchedChatCount > 0) {
    score += 0.1;
  }
  
  return Math.min(score, 1);
}
