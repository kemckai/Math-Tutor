# Logging System

The math tutor app now includes comprehensive logging to help with debugging and monitoring.

## Log Locations

**File logs:** `logs/app_YYYYMMDD.log` (one file per day)

## What Gets Logged

### Canvas & OCR
- Canvas render events
- "Interpret" button clicks  
- OCR preprocessing steps
- Recognized text results
- OCR failures and warnings
- Cache hits/misses

### Step Validation
- User step submissions
- Validation results (correct/incorrect)
- Reason codes for incorrect steps
- SymPy parsing failures
- OpenAI fallback attempts

### App Events
- Problem generation (concept, difficulty)
- Problem IDs and step counts
- Session state changes

## How to Use

**View logs in real-time (last 20 lines):**
```bash
tail -f logs/app_*.log
```

**Search for errors:**
```bash
grep ERROR logs/app_*.log
```

**Find OCR issues:**
```bash
grep "OCR" logs/app_*.log
```

**Find validation failures:**
```bash
grep "INCORRECT" logs/app_*.log
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (file only)
- **INFO**: General informational messages (file + console)
- **WARNING**: Warning messages (file + console)
- **ERROR**: Error messages (file + console)

## Example Log Entry

```
2026-03-19 14:32:15 | INFO     | ocr_image_to_text | recognition/ocr_processor.py:75 | Canvas OCR: result='x-0=3'
2026-03-19 14:32:16 | INFO     | validate_step | tutor/step_validator.py:410 | Validate: CORRECT (step_idx=0)
```
