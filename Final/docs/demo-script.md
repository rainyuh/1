# 演示脚本 · 雨夜公交站

> 两种展示方式：
> 1. **线性成品**：直接播放 `preview/rain_scene_demo.mp3`，这是已经混好的 75 秒版本。
> 2. **Soundcaster 现场演示**：在 Wwise 里按下面的顺序触发事件，录 30–60 秒。

## Soundcaster 演示顺序

打开 `Views > Soundcaster`，加载 `RainyBusStop` session。8 个按钮：

- `Play_AMB_RainShelter`
- `Play_AMB_RainStreet`
- `Play_SFX_CarPass`
- `Play_SFX_StoreDoor_Chime`
- `Play_SFX_EBike_Horn`
- `Play_SFX_Bus_AirBrakeDoor`
- `Stop_AMB_RainShelter`
- `Stop_AMB_RainStreet`

### 30–60 秒脚本

| 时间 | 操作 | 听感 |
|---|---|---|
| 0–5 s | 点 `Play_AMB_RainShelter` + `Play_AMB_RainStreet` | 顶棚近场雨 + 街道远场雨铺底 |
| 5–8 s | 点 `Play_SFX_StoreDoor_Chime` | 背后便利店的“叮咚” |
| 8–12 s | 点 `Play_SFX_CarPass` | 一辆车从远处驶过 |
| 12–15 s | 再点一次 `Play_SFX_CarPass` | Random Container 换一个车过变体 |
| 15–18 s | 点 `Play_SFX_EBike_Horn` | 便利店与站台之间的电瓶车 |
| 18–22 s | 点 `Play_SFX_Bus_AirBrakeDoor` | 公交进站、气刹、开门 |
| 22–26 s | 再点 `Play_SFX_CarPass` | 远处又一辆车 |
| 26–30 s | 点 `Play_SFX_StoreDoor_Chime` | 门铃第二次 |
| 30–35 s | 点 `Stop_AMB_RainShelter` + `Stop_AMB_RainStreet` | 收尾，雨声停止 |

> 车过多点几次，能听出 Random Container 在 3 个变体之间切换。
> 如果时间充裕，可以把每个事件之间多留 2–3 秒，让声音自然衰减。

## 录制

- 用 OBS 或 Windows 游戏栏（`Win + G`）录 30–60 秒。
- 录 Soundcaster 画面 + 声音；如果能同时展示 Game Object 3D Viewer 的 emitter/listener 移动更好。
- 视频放 GitHub Release 或 B 站，README 放链接。

## 如果不想录视频

- `preview/rain_scene_demo.mp3` 已经按同样顺序混好，可以直接作为“最终合成效果”提交。
- Soundcaster 截图 + 这段 MP3 也足够说明设计意图。

## 截图清单

| 文件名 | 内容 |
|---|---|
| `wwise-hierarchy.png` | Actor-Mixer 层级 |
| `wwise-loop.png` | 基底 Loop Infinite |
| `wwise-random-container.png` | RC_CarPass 的 Random / Step / Avoid Repeating |
| `wwise-positioning.png` | 3D Position + Attenuation |
| `wwise-soundcaster.png` | 8 个模块的 session |
