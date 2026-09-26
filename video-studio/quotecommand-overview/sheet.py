import json,subprocess,sys,os
FF = __import__("os").environ.get("FFMPEG") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
ids=sys.argv[1:]
os.makedirs("sheets",exist_ok=True)
for rid in ids:
    m=json.load(open(f"rec/{rid}/meta.json")); r=m["marks"].get("ready",0)/1000; e=m["marks"]["end"]/1000
    ts=[r+0.5+(e-r-1)*k/3 for k in range(4)]
    ins=[];
    for k,t in enumerate(ts): subprocess.run([FF,"-loglevel","error","-y","-ss",f"{t:.2f}","-i",f"rec/{rid}/raw.webm","-frames:v","1","-vf","scale=640:-2",f"sheets/{rid}_{k}.png"])
    subprocess.run([FF,"-loglevel","error","-y"]+sum([["-i",f"sheets/{rid}_{k}.png"] for k in range(4)],[])+["-filter_complex","[0][1]hstack[a];[2][3]hstack[b];[a][b]vstack","sheets/"+rid+".png"])
    print(rid, "ok" if m["ok"] else "FAIL", round(e-r,1),"s")
