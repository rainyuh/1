# 资产清单 · 雨夜公交站

> 场景：深秋夜里十点半，小雨到中雨，学校附近街角公交站，听者站在顶棚下、背对广告灯箱、面向马路。
> 所有交付资产：48 kHz / 24-bit / stereo WAV。

## 基底（2 条，40 s，循环）

| 文件 | 内容 | 时长 | LUFS | 用途 |
|---|---|---|---|---|
| `audio/ambience/AMB_Rain_Shelter_Loop_40s.wav` | 雨打站台顶棚，近场 | 40.0 s | -19.3 | 主基底，Loop Infinite |
| `audio/ambience/AMB_Rain_Street_Loop_40s.wav` | 雨打湿沥青 + 远处车流，远场 | 40.0 s | -25.1 | 铺底，比主基底低约 6 dB |

两条基底都做了环形交叉淡化：首尾样本连续，试听循环时不应出现“哒”声。街道基底保留了原素材的交通起伏，40 秒循环里有一次自然的车流涨落，不是接缝。

## 间断声（6 条）

| 文件 | 内容 | 时长 | LUFS | Wwise |
|---|---|---|---|---|
| `audio/one-shots/SFX_CarPass_Wet_01.wav` | 完整车过：由远及近再远去 | 8.0 s | -17.0 | RC_CarPass |
| `audio/one-shots/SFX_CarPass_Wet_02.wav` | 远距离车过，低通 2.5 kHz | 8.0 s | -18.2 | RC_CarPass |
| `audio/one-shots/SFX_CarPass_Wet_03.wav` | 近距离快速车过，水花大 | 4.0 s | -17.8 | RC_CarPass |
| `audio/one-shots/SFX_StoreDoor_Chime_01.wav` | 便利店自动门“叮咚”（5.5 kHz 低通 + 28% 混响，远处店内传来） | 1.7 s | -17.0 | 单独 Sound SFX，放在听者后方 8–12 m |
| `audio/one-shots/SFX_EBike_Horn_01.wav` | 电瓶车双音喇叭 | 0.65 s | -11.3 | 单独 Sound SFX |
| `audio/one-shots/SFX_Bus_AirBrake_Door_01.wav` | 公交气刹 + 开门 | 4.8 s | -18.5 | 单独 Sound SFX |

## 处理说明

- 基底：真实雨声裁切、正反向拼接、2 s / 4 s 交叉淡化、40 s 环形循环、20 Hz 高通（街道基底）。
- 车过：同一条真实车过录音的三个派生版本；02 做 2.5 kHz 低通模拟距离，03 取峰值段做近距离快速通过。
- 门铃：真实素材裁切、28% 混响（0.85 s）、5.5 kHz 低通、35 ms 淡入，峰值压到 -8 dBFS，做成“隔着店门、从店内向站台传来”的远距离感；电瓶车喇叭：裁切、淡入淡出、峰值归一化。
- 公交：从完整进站录音中截取 8.0–12.8 s 的气刹 + 开门段。
- 响度：基底按场景层次手工配平；间断声保留峰值余量，进 Wwise 后再用 Attenuation 和 Voice Volume 调整。

## 目录

```text
Final/
├─ audio/
│  ├─ ambience/
│  │  ├─ AMB_Rain_Shelter_Loop_40s.wav
│  │  └─ AMB_Rain_Street_Loop_40s.wav
│  └─ one-shots/
│     ├─ SFX_CarPass_Wet_01.wav
│     ├─ SFX_CarPass_Wet_02.wav
│     ├─ SFX_CarPass_Wet_03.wav
│     ├─ SFX_StoreDoor_Chime_01.wav
│     ├─ SFX_EBike_Horn_01.wav
│     └─ SFX_Bus_AirBrake_Door_01.wav
├─ docs/
│  ├─ asset-list.md
│  ├─ asset-manifest.json
│  ├─ sources.csv
│  └─ wwise-implementation.md
├─ images/
├─ preview/
│  ├─ rain_scene_demo.mp3
│  └─ wwise_soundcaster_demo.mp4
└─ tools/
   ├─ build_assets.py
   └─ build_preview.py
```

## 来源

素材来自 **BBC Sound Effects**、**爱给网（aigei.com）** 和 **耳聆网（ear0.com）**，仅用于课程作业；各网站的具体授权范围以网站条款为准。仓库中不包含原始素材文件，只保留处理后的成品资产。站点汇总见 `sources.csv`。
