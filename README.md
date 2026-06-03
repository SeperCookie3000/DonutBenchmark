# 🍩 DonutBenchmark

**A spinning 3D ASCII donut in your terminal — an honest single-core CPU benchmark**

## 🚀 How to run

1. Download `DonutBenchmark.exe`
2. Run the file
3. **Make the console window fullscreen** — the larger the window, the more accurate the test
4. Wait 30 seconds
5. Press `Ctrl+C` to stop and see your result

## 📊 What it measures

- **~2,000,000 math operations** per frame
- **~58,600 points** per frame
- Strictly **one CPU core** (Python GIL locks the rest)

Higher FPS = faster single-core performance.

## 🚨 Antivirus false positives

Some antiviruses (CrowdStrike, Bkav Pro, SecureAge) may **falsely** detect this file as malicious.

This happens because the program is packaged with PyInstaller. The code is completely safe — it's just a donut.
