#!/usr/bin/env python3
"""
ndbc_sanic.py serves NDBC (National Data Bouy Center) nine-band wave data and buoy metadata as JSON.
It uses the Sanic asynchronous server framework (similar to Flask)
Future development will serve all buoy data available on NDBC as JSON

Access the API through 2 endpoints:
/metadata
buoy ID, name, lat/lon, timezone
Add ?<buoyID> to retrieve metadata for 1 buoy
/ndbc/<buoyID>
Nine-band wave height and direction with timestamp and buoy station's metadata
"""

from ujson import dumps
import pytz
import sanic
import sanic_cors
import time
from datetime import datetime
from ndbc3 import metadata, ndbc3
from string import Template
import aiofiles
app = sanic.Sanic(__name__)

config = {
    # defaults
    "datatype": "9band",
    "buoy": "46232",
    "json": True,
    "datasource": "http",
    "units": "feet",
    "dt": "9band",
    "b": "46232",
    "ds": "http",
    "u": "feet",
    "callback": None
}

buoydata = []

async def get_metadata(app, loop):
    global buoydata
    buoydata = await metadata.metadata()
    print("metadata loaded")

@app.route("/metadata", methods=["GET"])
def send_meta(request):
    if len(request.args) is 0:
        return sanic.response.json(buoydata)
    params = sanitize_params(request.args)
    if params:
        try:
            if params['buoy']:
                data = [b for b in buoydata if b['id'] == params['buoy']]
                if len(data) > 0:
                    return sanic.response.json(data[0])
                else:
                    return sanic.response.text("Not Found", status=404)
        except BaseException as e:
            return sanic.response.text("Error", status=502)
            print(e)

@app.route("/ndbc/<buoyid>", methods=["GET"])
async def ndbc(request, buoyid):
    try:
        buoy_meta = [i for i in buoydata if i['id'] == buoyid][0]
        if buoy_meta:
            buoyname = buoy_meta['name']
        else:
            buoyname = buoyid
        async with aiofiles.open("./template/ndbc_template.html", loop=app.loop) as f:
            html = await f.read()
            t = Template(html).substitute(buoyname=buoyname, buoyid=buoyid)
        return sanic.response.html(t)
    except BaseException as e:
        print(e)
        return sanic.response.text("Error", status=500)

@app.route("/json", methods=["GET"])
async def json(request):
    print(request.args)
    params = sanitize_params(request.args)
    data = 'test'
    if params:
        try:
            params['json'] = True
            data = ndbc3.main(**params)
            # data = printstuff('stuff')
            metadata = [i for i in buoydata if i['id'] == params['buoy']]
            data['metadata'] = metadata[0]
            tz = data['metadata']['timezone']
            data['timestamp'] = ''.join(
                [data['timestamp'], ' ', datetime.now(pytz.timezone(tz)).strftime("%Z"), datetime.now(pytz.timezone(tz)).strftime('%z')])
            if params['callback']:
                data = ''.join([params['callback'], '(', dumps(data), ')'])
                return sanic.response.text(data)
            else:
                return sanic.response.json(data)
        except BaseException as e:
            print(e)
            return sanic.response.text("Error", status=500)

def sanitize_params(params):
    try:
        keys = list(config.keys())
        clean_params = {}
        if len(params) > 6:
            raise IOError('Error: More than 6 params given')
        for i in params.items():
            i = list(i)
            if i[0] in keys:
                if type(i[1]) is list:
                    i[1] = i[1][0]
                if str(i[1]).lower() == 'false':
                    i[1] = False
                if len(i[1]) > 10:
                    clean_params[i[0]] = i[1][:10]
                else:
                    clean_params[i[0]] = i[1]
        print(clean_params.keys())
        if 'callback' not in clean_params.keys():
            clean_params['callback'] = None
    except BaseException as e:
        print(e)
        return False
    return clean_params

@app.route("/test", methods=["GET"])
# @sanic_cors.cross_origin(app) # doesn't work with coroutines- only functions- for some reason
async def printstuff(stuff='foo'):
    time.sleep(10)
    return sanic.response.text(stuff)

app.static("/", "./")

app.run(host="0.0.0.0", port=3000, debug=True, before_start=get_metadata)
