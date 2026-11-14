# Wwise 实现 · 雨夜公交站

> 版本：Wwise **2025.1.11.9262**
> 工程名：`RainyBusStop`（不要用中文）
> 建议工程路径：`D:\wwise\RainyBusStop`，完成后再复制进仓库；Wwise 对中文路径可能出问题。

## 0. 当前工程状态

- 工程已建立：`wwise/RainyBusStop/RainyBusStop.wproj`，版本 2025.1.11.9262。
- 已通过 WAAPI 完成：层级、8 个资产导入、两条基底 Loop Infinite、`RC_CarPass`（Random / Step / Avoid Repeating 1）、4 个 Attenuation 及其 Volume/LPF 曲线、3D Position + Attenuation、8 个 Play/Stop 事件。
- `Soundcaster Sessions` 中已建立 `RainyBusStop`，并放入 6 个 Play + 2 个 Stop 按钮；打开工程后直接加载该 session 即可试听。
- 仍需在 Wwise GUI 中完成：试听、截图 5 张、录屏 30–60 s。
- 注意：WAAPI 里 Actor-Mixer Hierarchy 的路径是 `\Containers\Default Work Unit`，在 Wwise 界面里仍显示为 Actor-Mixer Hierarchy。

## 1. 导入资产

工程新建后，把 `audio/ambience/` 和 `audio/one-shots/` 里的 8 个 WAV 导入 `Default Work Unit`。

- 导入类型选 **Sound SFX**，不要 Sound Voice。
- 导入后检查 Source Editor 的采样率显示 `48000 Hz`、位深 `24`。
- 基底两条放在 `Ambience` 下，事件放在 `StreetEvents` 下。

```text
Actor-Mixer Hierarchy
└─ Default Work Unit
   ├─ Ambience
   │  ├─ AMB_Rain_Shelter_Loop
   │  └─ AMB_Rain_Street_Loop
   └─ StreetEvents
      ├─ RC_CarPass            (Random Container)
      │  ├─ SFX_CarPass_Wet_01
      │  ├─ SFX_CarPass_Wet_02
      │  └─ SFX_CarPass_Wet_03
      ├─ SFX_StoreDoor_Chime
      ├─ SFX_EBike_Horn
      └─ SFX_Bus_AirBrake_Door
```

## 2. 基底循环

两条基底都设置：

- General / Property Editor：勾选 **Loop**，Loop Count 设为 **Infinite**。
- Source Editor：确认循环起点为 0、终点为文件末尾；文件本身已经做过环形交叉淡化，一般不需要再改。
- 两条同时播放时，当前工程把两条基底都设为 **-5 dB**；远场 `AMB_Rain_Street_Loop` 的素材本身已比近场低约 6 dB，空间层次主要由素材电平建立。
- 基底是 2D 环境声：Positioning 里 3D Spatialization 选 **None**。

事件：

- `Play_AMB_RainShelter`
- `Play_AMB_RainStreet`
- `Stop_AMB_RainShelter`
- `Stop_AMB_RainStreet`

## 3. Random Container

`RC_CarPass`：

- 把 `SFX_CarPass_Wet_01/02/03` 拖进去。
- Playback Mode：**Step**（一次性触发）。
- Loop Count：**1**。
- 版本有 **Avoid Repeating** 时设为 **1**。
- Transition 保持默认 0 ms；三条素材已经做了等响度处理，随机切换不应有明显音量跳变。
- 事件：`Play_SFX_CarPass`。

门铃、电瓶车喇叭、公交不做 Random Container，直接作为单独 Sound SFX；各自建 `Play_...` 事件。

门铃素材已经做了 5.5 kHz 低通、28% 混响，峰值压到 -8 dBFS；Wwise 里再设 `Volume -5 dB`、`Lowpass 50%`，放在听者后方 8–12 m。电瓶车 `Volume -2 dB`，放在右侧非机动车道、便利店与站台之间 10–25 m。

## 4. Positioning 与 Attenuation

四个点声源分别放在不同方位，Soundcaster 里拖动时差异最直观：

| 声源 | 方位 | Attenuation | Max Distance |
|---|---|---|---|
| 车过积水 | 左/右车道 | `ATT_CarPass` | 80 m |
| 便利店门铃 | 听者背后偏右，8–12 m | `ATT_Chime` | 25 m |
| 电瓶车喇叭 | 右侧非机动车道，便利店与公交站之间，10–25 m | `ATT_Horn` | 60 m |
| 公交气刹 | 前方车道，15–25 m | `ATT_Bus` | 60 m |

每个 Sound / Random Container 的 Positioning 设置：

- 3D Spatialization：**Position**（点声源）。
- Listener Relative Routing：**开启**。
- Attenuation：选对应的 ShareSet。
- Center %：**0**。
- 车过可以开 Doppler；如果版本支持，在 Soundcaster / Game Object 3D Viewer 里拖动 emitter 听扫过的效果。
- 本机已验证 3D 版可直接试听；如果换机器后 3D 预览无声，用本地 2D 预览工程 `D:/wwiseproject/RainyBusStop_2D_Preview/RainyBusStop` 试听。

Attenuation 曲线示例（车过）：

- Volume：1 m 0 dB → 10 m -6 dB → 30 m -14 dB → 60 m -18 dB → 80 m -20 dB。
- Low-Pass Filter：**None**（本工程关闭，避免 2D 预览时发闷）。
- 末端保留 -20 dB 左右的可听电平，避免 Wwise 预览或远处把声音当成无声虚拟声部。
- 所有 one-shot 的 Advanced → Virtual Voice Behavior 设为 **Continue to play**。
- 雷声不在本次 6 条里；如果后面加，单独做 1000 m 的 ATT。

## 5. Soundcaster

Soundcaster Session `RainyBusStop` 已经建好，里面放了 8 个按钮：

- `Play_AMB_RainShelter`
- `Play_AMB_RainStreet`
- `Play_SFX_CarPass`
- `Play_SFX_StoreDoor_Chime`
- `Play_SFX_EBike_Horn`
- `Play_SFX_Bus_AirBrakeDoor`
- `Stop_AMB_RainShelter`
- `Stop_AMB_RainStreet`

打开工程后，在 Layouts 菜单里选 Soundcaster，加载 `RainyBusStop` session 即可。用 **Game Object 3D Viewer** 拖动 listener / emitter：

1. 先播放两条基底，确认顶棚近场与街道远场的比例。
2. 把车过 emitter 从左车道拖到右车道，听距离和声像变化。
3. 门铃放在 listener 背后，喇叭放在侧后方，公交放在前方。
4. 逐一触发事件，确认 Random Container 每次选到不同车过变体。

## 6. 截图与录屏清单

至少截 5 张：

1. Actor-Mixer 层级（能看到 Ambience / StreetEvents / RC_CarPass）。
2. 基底 Loop 设置（Loop Infinite）。
3. Random Container 设置（Step / Avoid Repeating）。
4. Positioning + Attenuation 曲线。
5. Soundcaster Session 播放状态。

录屏 30–60 s（OBS）：基底 → 车过 → 门铃 → 电瓶车喇叭 → 公交进站。视频放 GitHub Release 或 B 站，README 放链接。

## 7. `.gitignore`

```gitignore
# Wwise 用户设置 / 缓存 / 生成物
wwise/RainyBusStop/*.wsettings
wwise/RainyBusStop/*.prof
wwise/RainyBusStop/*.log
wwise/RainyBusStop/.cache/
wwise/RainyBusStop/Generated SoundBanks/

# 原始素材 / 工作文件
finalwork sound/
Final/.tmp_build/
Final/audio/_synthetic_backup/
Final/preview/audition/
```

注意：**不要**忽略 `*.wproj` 和 `*.wwu`，它们是工程和 Work Unit。`Originals/` 里是 Wwise 导入的源文件；如果仓库太大，再考虑 Git LFS 或只保留剪辑后的资产。
