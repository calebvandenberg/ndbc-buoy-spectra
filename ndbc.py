__author__ = 'Caleb'
from urllib2 import urlopen, HTTPError, URLError
import datetime
from math import sqrt
import numpy as np
import sys
from os import path
import json
import argparse

def localDataSpec(buoy):
    try:
        f = open(path.join('c:\\node', buoy + '.data_spec'), 'r')
        d = f.read(1024)
        f.close()
        return d.split('\n')[1]
    except IOError as e:
        sys.stderr.write(str(e))
        sys.exit(1)

def httpDataSpec(buoy, dataType='data_spec'):
    """fetches most recent buoy spectra observation from ndbc
       buoy id - the buoy
       dataType - can be 'data_spec', 'swdir', or 'swdir2' for energy, mean wave direction, or primary wave direction respectively"""

    dataUrl = ''.join(['http://www.ndbc.noaa.gov/data/realtime2/', buoy, '.', dataType])
    try:
        response = urlopen(dataUrl)
    except HTTPError, e:
        sys.stderr.write(str(e))
        sys.exit(1)
    except URLError, e:
        sys.stderr.write(str(e))
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
    d = response.read(1024)
    return d.split('\n')[1]


def arrayDataSpec(ds, e=[0,0,0,.028,.154,1.148,.28,.28,.168,.336,.924,1.4,.63,1.078,.756,1.302,.476,.364,
     .21,.196,.308,.266,.168,.154,.266,.252,.154,.224,.126,.112,.07,.07,.056,.042,.042,.028,.028,
     .014,.014,.014,.014,.014,.014,.014] + [0] * 20):
    """needs another data set to add new energy values to. e = energy density"""
    newds = [(en, i[1], i[2]) for en, i in zip(e, ds)]
    return newds

def data_spec(datas):
    """returns a list of tuples for each frequency band from raw data dump
    datas is straight out of httpDataSpec
    coded for energy but works with wave direction too.
    returns energy/direction, frequency, and bandwidth
    # sep_freq = '9.999'
    # datas = data.split(sep_freq)[1]
    # bandwidths = [.005,.0075,.01,.015,.2]"""

    l = []
    # semi-hacky way of determining if data is energy or direction
    if datas.find('(') > 23:
        dstart = 23
    else:
        dstart = 16
    datas = datas[dstart:].split(') ')
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
    # todo multiply e by bandwidth at each step instead of after function return
    print "high / low freq fences: " + str(round(1.0/fences[1], 1)) + "(" + str(round(fences[1], 6)) + ")" \
          + ' ' + str(round(1.0/fences[0], 1)) + "(" + str(round(fences[0], 6)) + ")"
    e = spec['e']
    f = spec['f']
    b = spec['b']
    i = 0
    if fences[1] == spec['f'][-1]:        # this is the shortest frequency so gonna use all of it
        partial1percent = 1
    else:
        while i < len(f):
            fend = f[i] - .5 * b[i]       # get low frequency / high period end of frequency band
            if round(fend, 3) > fences[1]:
                # i -= 1
                break
            elif round(fend, 3) == fences[1]:
                # print f[i], i
                i += 1
                break                     # i is index of last full band now
            i+=1
        partial1 = fend - fences[1]       # partial1 is band of spectra between low end of freq band and the high freq side of the fence
        partial1percent = partial1 / b[i] # find how much of the partial band we are taking, then multiply the energy by it. if fend & fences[1] are equal value of b[i] irrelevant: 0/x
    partial1e = e[i] * partial1percent    # if equal this will be zero
    partial1eb = partial1e * b[i]         # need to get the bandwidth part of the equation in here
    print "high freq fenced frequency band " + str(round(1.0/f[i], 1)) + "(" + str(round(f[i], 4)) + ") is " + str(round(partial1percent*100, 1)) + "%"
    # same as above for opposite end of fence
    j = 0
    if fences[0] == 1.0/40:
        partial2percent = 1
    else:
        while j < len(f):
            fbegin = f[j] + .5 * b[j]       # get high frequency / low period end of frequency band
            if round(fbegin, 3) > fences[0]:
                # j -= 1
                break
            elif round(fbegin, 3) == fences[0]:
                # print f[i], i
                j += 1
                break                     # i is index of last full band now
            j+=1
        partial2 = fbegin - fences[0]
        #     if round(f[j], 3) >= fences[0]:
        #         j -= 1
        #         # print f[j], j
        #         break
        #     j +=1
        # fbegin = f[j] + .5 * b[j]
        # partial2 = fbegin - fences[0]
        partial2percent = partial2 / b[j]
    partial2e = e[j] * partial2percent
    partial2eb = partial2e * b[j]
    print "low freq fenced frequency band " + str(round(1.0/f[j], 1)) + " (" + str(round(f[j], 4)) + ") is " + str(round(partial2percent*100, 1)) + "%"
    mide = np.sum(e[j+1:i]* b[j+1:i])     # add up energy * bandwidth for each freq
    fullBands = f[j+1:i]
    printFullBands = ''.join([str(round(1.0/fb,4)) + ' (' + str(round(fb,4)) + ') \n' for fb in fullBands])
    print "middle, full frequency bands: \n" + printFullBands
    bande = (partial2eb + mide + partial1eb) * 10000
    return bande

# def e():
#     e = [0,0,0,1.663,2.16,.648,.281,.346,.95,1.858,1.296,1.188,1.296,1.188,1.274,1.145,.389,.346,.302,.151,.13,.108,.086,.086,.086,.13,.065,.43,.086,.22,.22,.22,.22,
#          .22,.22,.22,.22,0,.22,.22,0,.22,0,0,0,0,0,0]
#     e= [0,0,0,2.511,2.7,.459,.432,.756,1.026,1.107,1.242,1.242,.891,.432,.648,.324,.351,.189,.108,.135,.081,.162,.081,.108,.054,.081,.054,.027,.054,.027,0,.027,.027] + [0]*13
#     e = [0]*6 + [.065,.52,.65,.1495,2.6,3.445,3.445,4.225,6.5,5.265,5.33,2.47,1.69,1.69,1.69,1.56,1.17,1.17,.52,.26,.585,.78,.325,.39,.455,.26,.26,.195,.13,.13,.13,.065,.13,.065] + [0]*4
#     # return e

class ndbcSpectra(object):
    def __init__(self, buoy='46232',datasource='http',e=[], **kwargs):
        self.buoy = buoy
        if datasource == 'local':
            self.data = localDataSpec(buoy)
        else:
            self.data = httpDataSpec(buoy)
            self.dataPDirection = httpDataSpec(buoy, 'swdir2')
            self.dataMDirection = httpDataSpec(buoy, 'swdir')
        self.el = []

        u = kwargs.get('units', 'ft') # default is to convert m to ft
        if u in ['m', 'metric', 'meters']:
            self.units = 1
        else:
            self.units = 3.28
        td = self.data[:23].split()
        self.timestamp = datetime.datetime(int(td[0]),int(td[1]),int(td[2]),int(td[3]))
        self.json = json.dumps({'buoy':self.buoy,'timestamp':self.timestamp.isoformat()})

        if e:
            ds = arrayDataSpec(data_spec(self.data),e)
        else:
            ds = data_spec(self.data)
        dsd = [d + (0,0) for d in ds] # faster to initialize 
        self.spectra = np.array(dsd,[('e', 'float16'),('f','float16'),('b','float16'),('pd','int16'),('md','int16')])
        self.spectra['pd'] = [i[0] for i in data_spec(self.dataPDirection)]
        self.spectra['md'] = [i[0] for i in data_spec(self.dataMDirection)]
        self.Hs = self.units*4*sqrt(np.sum(self.spectra['e']*self.spectra['b']))
        self.json = self.jsonify()

    def jsonify(self, dataType='spectra'):
        js = {'timestamp': self.timestamp.isoformat(' '), 'buoy': self.buoy, 'disclaimer': "Data in this object has not been validated and should be considered a placeholder"}
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
        return np.column_stack((self.units*4*np.sqrt(spectra['e']*spectra['b']), 1/spectra['f']))

    def nineBand(self):
        #                                   (0.04545-0.0425)/0.005 = 0.59 or 59%
        #                                    1.0/22 - spectra2['f'][5] - spectra2['b'][5] / spectra2['b'][5]
        # band22 = np.sum(spectra2['e'][0:4]) + (spectra2['e'][4] * (1.0/22 - (spectra2['f'][4]-.5 * spectra2['b'][4])) / spectra2['b'][4])
        spectra = self.spectra
        o = 1.0
        nineBands = (o/40,o/22,o/18,o/16,o/14,o/12,o/10,o/8,o/6,spectra['f'][-1])   # -.0025 used to subtract from spectra[f][-1]
        fence = 0
        energyList = []
        while fence < 9:
            energyList.append(band(spectra, (nineBands[fence], nineBands[fence+1]))) # removed 10000 * .005 from this line on 4/26/16
            fence +=1
        self.el = [round(2*4*self.units*.01*sqrt(int(v)), 2) for v in energyList]
        if __name__ != "__main__":
            print __name__
            print energyList
            print 'buoy: ', self.buoy
            print 'time: ', self.timestamp.isoformat()
            print '9-band: ', self.el
            print 'Hs: ', self.Hs
        return self.el

def main():
    parser = argparse.ArgumentParser(description='Process data from National Data Buoy Center (ndbc) buoys')
    parser.add_argument('--buoy', '-b', default='46232', help='Enter the buoy you want to access')
    parser.add_argument('--datasource', '-ds', default='http', choices=['http', 'local'], help='use http or local for remote / local data file')
    parser.add_argument('--json', action='store_true', help='return json data')
    parser.add_argument('--datatype', '-dt', choices=['spectra', '9band', 'hp'], help='returns raw buoy spectra, wave heights in 9 bands of wave periods, or wave heights and corresponding period')
    parser.add_argument('--units', '-u', choices=['m','metric','meters','feet','english','ft'], default='feet', help='Choose the units of measurement for wave heights')

    args = vars(parser.parse_args())
    bs = ndbcSpectra(**args)
    units = 3.28
    if args['units'] in ['m','metric','meters']:
        units = 1
    if args['json']:
        if args['datatype'] == 'spectra' or args['datatype'] is None:
            print bs.json
        elif args['datatype'] == '9band':
            print bs.jsonify('9band')
        elif args['datatype'] == 'hp':
            print bs.jsonify('hp')
    else:
        data = ''
        if args['datatype'] == 'spectra' or args['datatype'] is None:
            data =  bs.spectra
        elif args['datatype'] == '9band':
            data = bs.nineBand()
        elif args['datatype'] == 'hp':
            data = bs.heightPeriod()
        print data
        return data


if __name__ == "__main__":
    main()


