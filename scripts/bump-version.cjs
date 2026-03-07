/**
 * 版本号更新脚本
 *
 * 用法：
 *   node scripts/bump-version.cjs <版本号>
 *
 * 示例：
 *   node scripts/bump-version.cjs 2.3.0
 *
 * 会同时更新以下 3 个文件中的版本号：
 *   - package.json
 *   - src-tauri/tauri.conf.json
 *   - src-tauri/Cargo.toml
 */

const fs = require('fs');
const path = require('path');

const newVersion = process.argv[2];

if (!newVersion) {
  console.error('请指定版本号，例如: node scripts/bump-version.cjs 2.3.0');
  process.exit(1);
}

if (!/^\d+\.\d+\.\d+$/.test(newVersion)) {
  console.error(`版本号格式无效: "${newVersion}"，应为 x.y.z 格式（如 2.3.0）`);
  process.exit(1);
}

const root = path.resolve(__dirname, '..');

const files = [
  {
    path: path.join(root, 'package.json'),
    update(content) {
      const json = JSON.parse(content);
      const old = json.version;
      json.version = newVersion;
      return { result: JSON.stringify(json, null, 2) + '\n', old };
    },
  },
  {
    path: path.join(root, 'src-tauri', 'tauri.conf.json'),
    update(content) {
      const json = JSON.parse(content);
      const old = json.version;
      json.version = newVersion;
      return { result: JSON.stringify(json, null, 2) + '\n', old };
    },
  },
  {
    path: path.join(root, 'src-tauri', 'Cargo.toml'),
    update(content) {
      const match = content.match(/^version\s*=\s*"([^"]+)"/m);
      const old = match ? match[1] : '未知';
      const result = content.replace(
        /^version\s*=\s*"[^"]+"/m,
        `version = "${newVersion}"`
      );
      return { result, old };
    },
  },
];

console.log(`\n更新版本号 → ${newVersion}\n`);

for (const file of files) {
  const content = fs.readFileSync(file.path, 'utf-8');
  const { result, old } = file.update(content);
  fs.writeFileSync(file.path, result, 'utf-8');
  const relPath = path.relative(root, file.path);
  console.log(`  ${relPath}: ${old} → ${newVersion}`);
}

console.log('\n版本号更新完成。\n');
