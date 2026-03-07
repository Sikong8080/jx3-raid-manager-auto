/**
 * JX3 Raid Manager - Cloudflare Worker 更新代理
 *
 * 功能：代理 GitHub Releases 的更新请求，解决国内访问 GitHub 困难的问题。
 *
 * ========== 部署步骤 ==========
 *
 * 1. 登录 Cloudflare Dashboard: https://dash.cloudflare.com
 * 2. 左侧菜单 → Workers & Pages → Create Worker
 * 3. 给 Worker 起个名字（如 jx3-update-proxy），点击 Deploy
 * 4. 点击 "Edit code"，删除默认代码，粘贴本文件全部内容
 * 5. 点击 "Save and Deploy"
 * 6. 进入 Worker 页面 → Settings → Variables and Secrets，添加：
 *    - GITHUB_OWNER = Sikong8080
 *    - GITHUB_REPO  = jx3-raid-manager-auto
 * 7. 部署完成后，你会得到一个域名如: https://jx3-update-proxy.xxx.workers.dev
 * 8. 将该域名填入项目的 src-tauri/tauri.conf.json:
 *    "endpoints": ["https://jx3-update-proxy.xxx.workers.dev/update/latest.json", ...]
 *
 * 可选：绑定自定义域名
 * - Worker 页面 → Settings → Domains & Routes → Add → Custom Domain
 * - 输入你的域名（需要 DNS 在 Cloudflare 上）
 *
 * ========== API 路由 ==========
 *
 * GET /update/latest.json    → 代理 GitHub Release 的 latest.json，改写下载 URL 为 Worker 代理地址
 * GET /update/download/:file → 流式代理 GitHub Release 的安装包文件下载
 *
 * ==========  结束  ==========
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    const owner = env.GITHUB_OWNER || 'Sikong8080';
    const repo = env.GITHUB_REPO || 'jx3-raid-manager-auto';

    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    try {
      // 路由：获取更新清单
      if (path === '/update/latest.json') {
        return await handleLatestJson(owner, repo, url.origin);
      }

      // 路由：代理安装包下载
      if (path.startsWith('/update/download/')) {
        const fileName = decodeURIComponent(path.replace('/update/download/', ''));
        return await handleDownload(owner, repo, fileName);
      }

      // 其他路由：返回简单状态页
      return new Response(
        JSON.stringify({ status: 'ok', message: 'JX3 Raid Manager Update Proxy' }),
        { headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
      );
    } catch (err) {
      return new Response(
        JSON.stringify({ error: err.message || 'Internal Server Error' }),
        { status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
      );
    }
  },
};

/**
 * 代理 latest.json 并改写下载 URL
 */
async function handleLatestJson(owner, repo, workerOrigin) {
  const githubUrl = `https://github.com/${owner}/${repo}/releases/latest/download/latest.json`;

  const resp = await fetch(githubUrl, {
    headers: { 'User-Agent': 'JX3-Update-Proxy/1.0' },
    redirect: 'follow',
  });

  if (!resp.ok) {
    return new Response(
      JSON.stringify({ error: `GitHub 返回 ${resp.status}` }),
      { status: resp.status, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
    );
  }

  const data = await resp.json();

  // 改写 platforms 中的下载 URL，指向 Worker 代理
  if (data.platforms) {
    for (const platform of Object.keys(data.platforms)) {
      const info = data.platforms[platform];
      if (info.url) {
        // 从原始 GitHub URL 中提取文件名
        const urlParts = info.url.split('/');
        const fileName = urlParts[urlParts.length - 1];
        info.url = `${workerOrigin}/update/download/${encodeURIComponent(fileName)}`;
      }
    }
  }

  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      ...corsHeaders(),
    },
  });
}

/**
 * 流式代理 GitHub Release 文件下载
 */
async function handleDownload(owner, repo, fileName) {
  // 先获取最新 release 的 tag
  const releaseApiUrl = `https://api.github.com/repos/${owner}/${repo}/releases/latest`;
  const releaseResp = await fetch(releaseApiUrl, {
    headers: {
      'User-Agent': 'JX3-Update-Proxy/1.0',
      'Accept': 'application/vnd.github.v3+json',
    },
  });

  if (!releaseResp.ok) {
    return new Response(
      JSON.stringify({ error: `获取 Release 信息失败: ${releaseResp.status}` }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
    );
  }

  const release = await releaseResp.json();
  const tagName = release.tag_name;

  // 构造 GitHub 下载 URL
  const downloadUrl = `https://github.com/${owner}/${repo}/releases/download/${tagName}/${fileName}`;

  const fileResp = await fetch(downloadUrl, {
    headers: { 'User-Agent': 'JX3-Update-Proxy/1.0' },
    redirect: 'follow',
  });

  if (!fileResp.ok) {
    return new Response(
      JSON.stringify({ error: `文件下载失败: ${fileResp.status}` }),
      { status: fileResp.status, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
    );
  }

  // 流式转发文件
  return new Response(fileResp.body, {
    headers: {
      'Content-Type': fileResp.headers.get('Content-Type') || 'application/octet-stream',
      'Content-Length': fileResp.headers.get('Content-Length') || '',
      'Content-Disposition': `attachment; filename="${fileName}"`,
      ...corsHeaders(),
    },
  });
}

/**
 * CORS 响应头
 */
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
