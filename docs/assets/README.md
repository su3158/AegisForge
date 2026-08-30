# README screenshots

Generate these from the real React UI:

```powershell
$env:AEGISFORGE_CAPTURE_SCREENSHOTS = "1"
corepack pnpm --dir apps/web test --grep "captures README screenshots"
Remove-Item Env:\AEGISFORGE_CAPTURE_SCREENSHOTS
```

Expected files:

- `aegisforge-dashboard.png`
- `aegisforge-new-target.png`
- `aegisforge-scan-wizard.png`
- `aegisforge-evidence.png`
- `aegisforge-coverage.png`
