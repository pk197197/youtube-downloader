v1.1.1
1. 选择画质后未能按预期下载
2. 复制链接后直接按下载(未选画质，未改保存路径，默认最高，默认下载路径),下方会提示warning，虽然再等一会还是会弹出下载完成，但是无法感知，应该要有进度和目前汇报

log如下：
[19:45:43] 程序已就绪，请粘贴链接或点击按钮开始。
[19:45:52] 🔍 开始解析链接: https://www.youtube.com/watch?v=rK3ReLs6y7Y
[19:45:55] ✅ 解析成功: 山西菜真的上不得台面吗？
[19:45:55] 请选择画质和保存路径，然后点击下载。
[19:45:56] 🚀 开始下载任务...
[19:45:56] 正在连接下载服务器...
[19:46:00] ⚠️ [youtube] [jsc] Remote components challenge solver script (deno) and NPM package (deno) were skipped. These may be required to solve JS challenges. You can enable these downloads with  --remote-components ejs:github  (recommended) or  --remote-components ejs:npm , respectively. For more information and alternatives, refer to  https://github.com/yt-dlp/yt-dlp/wiki/EJS
[19:46:00] ⚠️ [youtube] rK3ReLs6y7Y: n challenge solving failed: Some formats may be missing. Ensure you have a supported JavaScript runtime and challenge solver script distribution installed. Review any warnings presented before this message. For more details, refer to  https://github.com/yt-dlp/yt-dlp/wiki/EJS
[19:46:27] ✅ 文件下载完成，正在进行后期处理（合并/转码）...
[19:46:32] ✅ 文件下载完成，正在进行后期处理（合并/转码）...
[19:46:32] 🎉 所有任务执行成功！

3. 画质选项应是1.最高画质，2.1080o，3.720p(目前只有最高画质有序号，其他都没有序号)

