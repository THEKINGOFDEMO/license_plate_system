<template>
  <div class="diagram-shell">
    <svg class="architecture-svg" viewBox="0 0 1120 560" role="img" aria-label="系统架构图">
      <defs>
        <linearGradient id="archUserBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fff8ef" />
          <stop offset="100%" stop-color="#f6ecdf" />
        </linearGradient>
        <linearGradient id="archFrontendBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#eff8f4" />
          <stop offset="100%" stop-color="#e3f1eb" />
        </linearGradient>
        <linearGradient id="archBackendBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#edf7f2" />
          <stop offset="100%" stop-color="#dcefe7" />
        </linearGradient>
        <linearGradient id="archModelBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#f8f8ee" />
          <stop offset="100%" stop-color="#ecefdd" />
        </linearGradient>
        <linearGradient id="archStorageBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fff9f1" />
          <stop offset="100%" stop-color="#f3eadf" />
        </linearGradient>
        <filter id="archShadow" x="-20%" y="-20%" width="140%" height="160%">
          <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="rgba(55,33,14,0.14)" />
        </filter>
      </defs>

      <g>
        <rect x="420" y="28" width="280" height="86" rx="24" fill="url(#archUserBg)" stroke="rgba(95,72,46,0.14)" filter="url(#archShadow)" />
        <text x="560" y="64" text-anchor="middle" fill="#34261c" font-size="28" font-weight="700">用户</text>
        <text x="560" y="92" text-anchor="middle" fill="#6e5846" font-size="16">浏览器访问、图片上传、结果查询</text>
      </g>

      <g>
        <rect x="350" y="170" width="420" height="112" rx="28" fill="url(#archFrontendBg)" stroke="rgba(95,72,46,0.14)" filter="url(#archShadow)" />
        <text x="560" y="210" text-anchor="middle" fill="#34261c" font-size="28" font-weight="700">Vue 前端</text>
        <text x="560" y="244" text-anchor="middle" fill="#6e5846" font-size="17">登录页、首页总览、图片识别、历史记录、系统说明</text>
      </g>

      <g>
        <rect x="300" y="338" width="520" height="120" rx="30" fill="url(#archBackendBg)" stroke="rgba(95,72,46,0.14)" filter="url(#archShadow)" />
        <text x="560" y="382" text-anchor="middle" fill="#34261c" font-size="28" font-weight="700">Django 后端</text>
        <text x="560" y="416" text-anchor="middle" fill="#6e5846" font-size="17">/api/health/  /api/stats/  /api/recognize/  /api/records/</text>
      </g>

      <g>
        <rect x="86" y="338" width="170" height="120" rx="26" fill="url(#archModelBg)" stroke="rgba(95,72,46,0.14)" filter="url(#archShadow)" />
        <text x="171" y="382" text-anchor="middle" fill="#34261c" font-size="24" font-weight="700">YOLO / CRNN</text>
        <text x="171" y="414" text-anchor="middle" fill="#6e5846" font-size="15">车牌检测</text>
        <text x="171" y="438" text-anchor="middle" fill="#6e5846" font-size="15">字符识别</text>
      </g>

      <g>
        <rect x="866" y="338" width="170" height="120" rx="26" fill="url(#archStorageBg)" stroke="rgba(95,72,46,0.14)" filter="url(#archShadow)" />
        <text x="951" y="382" text-anchor="middle" fill="#34261c" font-size="24" font-weight="700">SQLite / media</text>
        <text x="951" y="414" text-anchor="middle" fill="#6e5846" font-size="15">历史记录</text>
        <text x="951" y="438" text-anchor="middle" fill="#6e5846" font-size="15">上传图与结果图</text>
      </g>

      <path d="M 560 114 V 158" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />
      <path d="M 560 158 l -10 -12 M 560 158 l 10 -12" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />

      <path d="M 560 282 V 326" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />
      <path d="M 560 326 l -10 -12 M 560 326 l 10 -12" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />

      <path d="M 300 398 H 268" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />
      <path d="M 268 398 l 12 -10 M 268 398 l 12 10" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />

      <path d="M 820 398 H 854" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />
      <path d="M 854 398 l -12 -10 M 854 398 l -12 10" fill="none" stroke="#8ab7a5" stroke-width="4" stroke-linecap="round" />
    </svg>
  </div>
</template>
