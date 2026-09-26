import edit, re
real = edit.run; import os; edit.os.replace = lambda a, b: None
edit.run = lambda *a, **k: None        # skip re-rendering video items
items, total, vo_events, captions = edit.build()
edit.run = real
src = open("edit.py").read()
main = src.split('if __name__ == "__main__":')[1]
main = main.replace("items, total, vo_events, captions = build()", "").replace('concat(items, f"{OUT}/video.mp4")', "")
main = "\n".join(l[4:] if l.startswith("    ") else l for l in main.splitlines())
exec(main, {**vars(edit), "items": items, "total": total, "vo_events": vo_events, "captions": captions})
