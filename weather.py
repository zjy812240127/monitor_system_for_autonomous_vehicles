import json
import threading
latlng=(
	{
		"lng":"120.04536673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04546673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04556673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04566673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04576673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04586673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04596673206613",
		"lat":"30.234632381748856" 
	},
	{
		"lng":"120.04606673206613",
		"lat":"30.234632381748856" 
	},
)
i=0
def fun_time():
	global i
	with open("weather.json","w",encoding='utf-8') as f:
		f.write(json.dumps(latlng[i],indent=4))
		i=i+1
		if i>7:
			i=0
	global timer
	timer=threading.Timer(3,fun_time)
	timer.start()
timer=threading.Timer(3,fun_time)
timer.start()
	
