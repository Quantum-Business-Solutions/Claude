import json, subprocess, glob, os
from faster_whisper import WhisperModel
FF = __import__("os").environ.get("FFMPEG") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
m=WhisperModel('base.en',compute_type='int8')
durs={}; tot=0
for f in sorted(glob.glob('s*.mp3')):
    out=subprocess.run([FF,'-hide_banner','-i',f,'-f','null','-'],capture_output=True,text=True).stderr
    d=[l for l in out.splitlines() if 'Duration' in l][0].split('Duration: ')[1].split(',')[0]
    h,mi,s=d.split(':'); sec=int(h)*3600+int(mi)*60+float(s); durs[f[:3]]=sec; tot+=sec
    segs,_=m.transcribe(f); txt=' '.join(x.text.strip() for x in segs)
    print(f[:3], round(sec,1), txt[:150])
json.dump(durs,open('../vo_durations.json','w'),indent=1)
print('TOTAL', round(tot/60,2),'min', len(durs))
