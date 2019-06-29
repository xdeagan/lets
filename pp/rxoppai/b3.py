import json
import os
import subprocess


def runOppaiProcess(command):
	process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	output = json.loads(process.stdout.decode("utf-8", errors="ignore"))
	if "code" not in output or "errstr" not in output:
		print("oof")
	if output["code"] != 200:
		print("oof")
	if "pp" not in output or "stars" not in output:
		print("oof")
	pp = output["pp"]
	stars = output["stars"]

	return pp, stars

command = "./oppai {}".format("../../.data/beatmaps/55.osu")
command += " {acc:.2f}%".format(acc=99.6)
command += " +{mods}".format(mods="HDHR")
command += " {combo}x".format(combo=500)
command += " {misses}xm".format(misses=1)
command += " -ojson"

pp = 0.00
stars = 0.00
pp, stars = runOppaiProcess(command)
print(pp)