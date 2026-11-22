"""EXPLORATORY chain (after the LoRA verdict): wrong-rule lr 3e-4 and 1e-3 (seed 0); wrong-rule
seeds 1,2 and neutral seeds 1,2 at each arm's seed-0-chosen lr. One process at a time, same
settings as the method runs. Neutral seeds are dropped if this chain's cumulative wall time
passes 3 h (logged). Commits (local + push) after each run."""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
LORA = os.path.join(common.ROOT, "demo_out", "lora")
LRS = (1e-4, 3e-4, 1e-3)
LIMIT_H = 3.0
t0 = time.time()
rid = lambda arm, lr, s: f"{arm}_lr{lr:.0e}_s{s}"
done = lambda arm, lr, s: os.path.exists(os.path.join(LORA, rid(arm, lr, s) + ".json"))
GIT = ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]


def sh(cmd):
  return subprocess.run(cmd, cwd=common.ROOT, capture_output=True, text=True)


def launch(arm, lr, s):
  if done(arm, lr, s):
    return
  with open(os.path.join(common.ROOT, "logs", f"demo_lora_{rid(arm, lr, s)}.log"), "w") as f:
    rc = subprocess.run([sys.executable, "demo/lora.py", "--arm", arm, "--perm", "0", "--lr", str(lr), "--seed", str(s), "--rank", "4"],
                        stdout=f, stderr=subprocess.STDOUT, cwd=common.ROOT).returncode
  if rc != 0 or not done(arm, lr, s):
    raise SystemExit(f"run {rid(arm, lr, s)} failed (exit {rc})")
  sh([sys.executable, "demo/ledger.py"])
  sh(["git", "add", f"demo_out/lora/{rid(arm, lr, s)}.json", "RESULTS_LEDGER.md", "demo_out/ledger.json"])
  sh(["git", "commit", "-q", "-m", f"exploratory run {rid(arm, lr, s)}", "-m",
      "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SjA2UwPwxQicQ6boGHZXU2"])
  if sh(GIT + ["push", "-q", "origin", "demo"]).returncode != 0:
    sh(GIT + ["pull", "-q", "--rebase", "--autostash", "origin", "demo"])
    sh(GIT + ["push", "-q", "origin", "demo"])
  print(f"[done] {rid(arm, lr, s)} at {(time.time() - t0) / 3600:.2f} h", flush=True)


def chosen(arm):
  v = {lr: json.load(open(os.path.join(LORA, rid(arm, lr, 0) + ".json")))["tune_best"]["soft_regret"] for lr in LRS if done(arm, lr, 0)}
  if len(v) < 3:
    raise SystemExit(f"{arm} grid incomplete")
  return min(v, key=lambda k: (v[k], k))


for lr in (3e-4, 1e-3):
  launch("wrong_rule", lr, 0)
wr = chosen("wrong_rule")
print(f"wrong_rule chosen lr {wr:.0e}", flush=True)
for s in (1, 2):
  launch("wrong_rule", wr, s)
nl = chosen("neutral")
for s in (1, 2):
  if (time.time() - t0) / 3600 > LIMIT_H:
    print(f"DROPPED neutral seed {s}: chain wall time over {LIMIT_H} h", flush=True)
    continue
  launch("neutral", nl, s)
print("EXPLORE CHAIN DONE", flush=True)
