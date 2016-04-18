__author__ = 'Caleb'
from urllib2 import urlopen
import datetime
from math import sqrt
import numpy as np
import sys
from os import path
import json
import argparse

def localDataSpec(buoy):
    f = open(path.join('c:\\node', buoy + '.data_spec'), 'r')
    d = f.read(1024)
    f.close()
    return d.split('\n')[1]

def httpDataSpec(buoy):
    dataUrl = ''.join(['http://www.ndbc.noaa.gov/data/realtime2/', buoy, '.data_spec'])
    response = urlopen(dataUrl)
    d = response.read(1024)
    return d.split('\n')[1]

def arrayDataSpec(ds, e=[0,0,0,.028,.154,1.148,.28,.28,.168,.336,.924,1.4,.63,1.078,.756,1.302,.476,.364,
     .21,.196,.308,.266,.168,.154,.266,.252,.154,.224,.126,.112,.07,.07,.056,.042,.042,.028,.028,
     .014,.014,.014,.014,.014,.014,.014] + [0] * 20):
    """needs another data set to add new energy values to. e = energy density"""
    newds = [(en, i[1], i[2]) for en, i in zip(e, ds)]
    return newds

def data_spec(datas):
    # sep_freq = '9.999'
    # datas = data.split(sep_freq)[1]
    # bandwidths = [.005,.0075,.01,.015,.2]
    l = []
    datas = datas[23:].split(') ')
    i=0
    while i < len(datas):
    # for i in datas.split(') '):
        if datas[i]:
            t = datas[i].split()
            e = float(t[0])
            f = float(t[1].strip('()'))
            if i is 0:
                b = .005
            else:
                b = f - l[i-1][1]
                # b2 = {j: abs(b1-j) for j in bandwidths}
                # v = b2.values()
                # k = b2.keys()
                # b = k[v.index(min(v))]
            l.append((e,f,b))
        i+=1
    return l

def band(spec, fences):
    """spec is multidim numpy array, fences is tuple containing high and low frequency for band"""
    e = spec['e']
    f = spec['f']
    b = spec['b']
    i = 0
    while i < len(f):
        if round(f[i], 3) >= fences[1]:
            i -= 1
            # print f[i], i
            break
        i+=1
    fend = f[i] - .5 * b[i]
    partial1 = fences[1] - fend
    partial1percent = partial1 / b[i]
    partial1e = e[i] * partial1percent
    j = 0
    if fences[0] == 1.0/40:
        partial2percent = 1
    else:
        while j < len(f):
            if round(f[j], 3) >= fences[0]:
                j -= 1
                # print f[j], j
                break
            j +=1
        fbegin = f[j] - .5 * b[j]
        partial2 = fences[0] - fbegin
        partial2percent = partial2 / b[j]
    partial2e = e[j] * partial2percent
    mide = np.sum(e[j+1:i])
    bande = partial2e + mide + partial1e
    return bande

def e():
    e = [0,0,0,1.663,2.16,.648,.281,.346,.95,1.858,1.296,1.188,1.296,1.188,1.274,1.145,.389,.346,.302,.151,.13,.108,.086,.086,.086,.13,.065,.43,.086,.22,.22,.22,.22,
         .22,.22,.22,.22,0,.22,.22,0,.22,0,0,0,0,0,0]
    e= [0,0,0,2.511,2.7,.459,.432,.756,1.026,1.107,1.242,1.242,.891,.432,.648,.324,.351,.189,.108,.135,.081,.162,.081,.108,.054,.081,.054,.027,.054,.027,0,.027,.027] + [0]*13
    e = [0]*6 + [.065,.52,.65,.1495,2.6,3.445,3.445,4.225,6.5,5.265,5.33,2.47,1.69,1.69,1.69,1.56,1.17,1.17,.52,.26,.585,.78,.325,.39,.455,.26,.26,.195,.13,.13,.13,.065,.13,.065] + [0]*4
    return e

class ndbcSpectra(object):
    def __init__(self, buoy='46232',datasource='http',e=[], **kwargs):
        self.buoy = buoy
        if datasource is 'local':
            self.data = localDataSpec(buoy)
        else:
            self.data = httpDataSpec(buoy)
        self.Hs = 0
        self.el = []
        td = self.data[:23].split()
        self.timestamp = datetime.datetime(int(td[0]),int(td[1]),int(td[2]),int(td[3]))
        self.json = json.dumps({'buoy':self.buoy,'timestamp':self.timestamp.isoformat()})

        if e:
            ds = arrayDataSpec(data_spec(self.data),e)
        else:
            ds = data_spec(self.data)

        self.spectra = np.array(ds,[('e', 'float16'),('f','float16'),('b','float16')])
        self.json = self.jsonify()

    def jsonify(self, dataType='spectra'):
        js = {'timestamp': self.timestamp.isoformat(' '), 'buoy': self.buoy}
        jsList = []
        digits = 3
        if dataType is 'spectra':
            b = self.spectra.tolist()
            keys = ['energy density', 'frequency', 'bandwidth', 'period']
            for i in b:
                ip = list(i)
                ip.append(1.0/i[1])
                dip = {k:round(d,digits) for k, d in zip(keys, ip)}
                jsList.append(dip)
        elif dataType is '9band':
            b = self.nineBand()
            keys = ['22+','20','17','15','13','11','9','7','4']
            jsList = {k:v for k,v in zip(keys,b)}
        elif dataType in ['hp', 'heightPeriod']:
            b = self.heightPeriod()
            jsList = {round(p,digits):round(h,digits) for p,h in zip(b[:,1],b[:,0])}

        js[dataType] = jsList

        return json.dumps(js)

    def heightPeriod(self):
        """takes numpy energy, frequency, bandwidth array and returns the height for each spectral band
        waverider buoys return 64 bands, others return ~46"""
        # hp = 3.28*4*np.sqrt(spectra2['e']*spectra2['b'])
        spectra = self.spectra
        return np.column_stack((3.28*4*np.sqrt(spectra['e']*spectra['b']), 1/spectra['f']))

    def nineBand(self):
        #                                   (0.04545-0.0425)/0.005 = 0.59 or 59%
        #                                    1.0/22 - spectra2['f'][5] - spectra2['b'][5] / spectra2['b'][5]
        # band22 = np.sum(spectra2['e'][0:4]) + (spectra2['e'][4] * (1.0/22 - (spectra2['f'][4]-.5 * spectra2['b'][4])) / spectra2['b'][4])
        spectra = self.spectra
        o = 1.0
        nineBands = (o/40,o/22,o/18,o/16,o/14,o/12,o/10,o/8,o/6,spectra['f'][-1]-.0025)
        fence = 0
        energyList = []
        while fence < 9:
            energyList.append(band(spectra, (nineBands[fence], nineBands[fence+1])) * 10000 * .005)
            fence +=1
        self.el = [round(2*4*.0328*sqrt(int(v)), 2) for v in energyList]
        self.Hs = 3.28*4*sqrt(np.sum(spectra['e']*spectra['b']))
        if __name__ != "__main__":
            print __name__
            print energyList
            print 'buoy: ', self.buoy
            print 'time: ', self.timestamp.isoformat()
            print '9-band: ', self.el
            print 'Hs: ', self.Hs
        return self.el

def main():
    # if argv is None:
    #     argv = sys.argv[1]


    parser = argparse.ArgumentParser(description='Process data from National Data Buoy Center (ndbc) buoys')
    parser.add_argument('--buoy', '-b', help='Enter the buoy you want to access')
    parser.add_argument('--datasource', '-ds', choices=['http', 'local'], help='use http or local for remote / local data file')
    parser.add_argument('--json', action='store_true', help='return json data')
    parser.add_argument('--datatype', '-dt', choices=['spectra', '9band', 'hp'], help='returns raw buoy spectra, wave heights in 9 bands of wave periods, or wave heights and corresponding period')

    args = vars(parser.parse_args())
    bs = ndbcSpectra(**args)
    if args['json']:
        if args['datatype'] == 'spectra' or args['datatype'] is None:
            print bs.json
        elif args['datatype'] == '9band':
            print bs.jsonify('9band')
        elif args['datatype'] == 'hp':
            print bs.jsonify('hp')
    else:
        if args['datatype'] == 'spectra':
            data =  bs.spectra
        elif args['datatype'] == '9band':
            data = bs.nineBand()
        elif args['datatype'] == 'hp':
            data = bs.heightPeriod()
        print data
        return data

if __name__ == "__main__":
    main()


def junk():
    return
    if "test" in argv:
        print argv

    buoy = '46232'
    for i in argv:
        i = ''.join(c for c in i if c.isalnum())
        if i.isdigit() and len(i) is 5:
            buoy = i

    bs = ndbcSpectra(*argv[1:])
    print bs.jsonify('9band')
    return

    if 'json' in argv:
        bs = ndbcSpectra(buoy)
        if '9band' in argv:
            return bs.jsonify('9band')
        elif argv in ['hp', 'heightPeriod']:
            return bs.jsonify('hp')
        else:
            return bs.jsonify('spectra')
    if "local" in argv:
        bs = ndbcSpectra(buoy, 'local')
        print bs.spectra
        return
    else:
        bs = ndbcSpectra(buoy)
        print bs.spectra

    if '9band' in argv:
        bs.nineBand()
    if 'hp' in argv:
        print bs.heightPeriod()

    # if "iter" in argv:
    #     iterForecast()
    # elif len(argv) == 2 and len(argv[1]) <= 12:
        # con = mdb.connect('localhost', read_default_file="/home/monty/conf/.monty.cnf", db='calebv_swellmatrix')
        # cur = con.cursor()
        # cur.execute('select `name`, `timeZone` from `buoys` WHERE `id` = "%s"' % argv[1])
        # (buoyName, tz) = cur.fetchone()
        # if buoyName:
        #     printDump(argv[1], dump(argv[1], tz))
        #     writeForecastHTML(argv[1], buoyName)
        # else:
        #     print "invalid buoy"
        # con.close()
    # elif len(argv) <= 1:




##########################
def oldstuff():
    buoy = '191'
    dataUrl = 'http://www.ndbc.noaa.gov/data/realtime2/%s.swr2' % buoy
    dataUrl = 'http://cdip.ucsd.edu/data_access/justdar.cdip?%s+sp' % buoy
    opener = URLopener()
    # data = opener.open(dataUrl).readlines()[1] # grab first line of data only

    # tstamp = datetime.datetime.strptime(data[:16], "%Y %m %d %H %M")
    # period (T) = 1/ freq
    wfile = opener.open(dataUrl).readlines()
    tstamp = datetime.datetime.strptime(wfile[0][23:35], "%Y%m%d%H%M")
    data = wfile[10:-1]
    freq, period, bandwidth, energy = [],[],[],[]

    def getCSV(filestr='c:/wamp/www/monty/swellmatrix scraps/data%s.csv' % buoy):
        f = open(filestr, 'r')
        data = f.readlines()
        freq, period, bandwidth, energy = [],[],[],[]
        for i in data:
            d = i.split(',')
            freq.append( round(float(d[0]), 4))
            period.append(round(1/float(d[0]),2))
            bandwidth.append(float(d[1]))
            energy.append(float(d[2]))
        f.close()
        return np.array([freq,period,bandwidth,energy])

    x = getCSV()
    energyBin = {'22+': None, '20': None, '17': None, '15': None, '13': None, '9': None, '7': None, '4': None}
    fences = [1.0/40, 1.0/22, 1.0/20, 1.0/18, 1.0/16, 1.0/14, 1.0/12, 1.0/10, 1.0/8, 1.0/6, 1.0/2]



    for i in data:
       d = i.split()
       freq.append( round(float(d[0]), 4))
       period.append(round(1/float(d[0]),2))
       bandwidth.append(float(d[1]))
       energy.append(float(d[2]))
    i=0
    h=[]
    while i < len(freq):
        h.append(round(energy[i]*bandwidth[i]*10000,3))
        i+=1
    height = [round(2*4*.0328*sqrt(v), 2) for v in h]
    f = open('c:/wamp/www/monty/swellmatrix scraps/data%s.csv' % buoy, 'w')
    for i in zip(period, h, height):
        f.write("%s,%s,%s\n" % i)
    f.close()

    energyBin = {'22+': None, '20': None, '17': None, '15': None, '13': None, '9': None, '7': None, '4': None}

    energyBin['22+'] = (sum(energy[:3]) + energy[4]*((1/22.0)-(freq[4]-(bandwidth[4]*.5)))/bandwidth[4])*.005*10000
    energyBin['20'] = (energy[4]*((freq[4]+bandwidth[4]*.5-(1/22.0))/bandwidth[4]) + energy[5] + energy[6]*((1/18.0)-(freq[6]-(bandwidth[6]*.5)))/bandwidth[6])*.005*10000
    energyBin['17'] = ((energy[6]*(freq[6]+(bandwidth[6]*.5-(1/18.0)))/bandwidth[6]) + energy[7])/.005*10000

    # bandrange = []
    # bandrange[0] = bandwidth[4]*.5+freq[4]
    # bandrange[1] =

