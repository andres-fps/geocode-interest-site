import json
import math
import PyV8
import psycopg2
import sys
import urllib

from pyproj import Proj, transform

conn = ''
poiName = ''
googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'

def closeDBConnection():
    conn.close()

def connectToDB():
    try:
        global conn
        conn = psycopg2.connect("dbname='gisdb' user='postgres' host='localhost' password='nemesis'")
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users_x_points_of_interest')
        cursor.execute('DELETE FROM points_of_interest_como')
        cursor.execute('ALTER SEQUENCE points_of_interest_como_gid_seq RESTART WITH 1')
        #cursor.execute('DELETE FROM users')
        #cursor.execute('ALTER SEQUENCE users_uid_seq RESTART WITH 1')
    except:
       print "I am unable to connect to the database"		

def getUTMCoordinates(lat, lon):
    inProj = Proj(init='epsg:4326')
    outProj = Proj(init='epsg:32632')
    xutm, yutm = transform(inProj, outProj, lat, lon)
    print xutm, yutm

def insertUsers():
    usersDictionary = ({"first_name":"Joshua", "last_name":"Drake", "country":"Italy", "occupation":"Student"},
                       {"first_name":"Steven", "last_name":"Foo", "country":"Italy", "occupation":"Student"},
                       {"first_name":"David", "last_name":"Bar", "country":"Italy", "occupation":"Student"})
					   
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO users(first_name, last_name, country, occupation) VALUES (%(first_name)s, %(last_name)s, %(country)s, %(occupation)s)', usersDictionary)
    
	#Finalize connection and cursor objects
    cursor.close()
    conn.commit()
	
def insertPointOfInterest(xutm, yutm):    
    cursor = conn.cursor()
    cursor.execute('SELECT ST_MakePoint (%s, %s)', (xutm, yutm))
    geometry = cursor.fetchone()
    cursor.execute('INSERT INTO points_of_interest_como (name, geom) VALUES (%s, %s)', (poiName, geometry[0]))
    print cursor.statusmessage
    print '----------------------------------------------------------------'
	
	#Finalize connection and cursor objects
    cursor.close()
    conn.commit()
	
def getUTMCoordinatesFromJS(lat, lon):
    ctxt = PyV8.JSContext()
    ctxt.enter()
	
    jsfile = open('UTMConverter.js')
    stream = jsfile.read()
    jsfile.close()
	
    ctxt.eval(stream)
    jsfunction = 'dec2utm(' + str(lat) + ',' + str(lon) + ')'
    utmvalues = ctxt.eval(jsfunction)
    xutm, yutm = utmvalues[2], utmvalues[3]
    print 'UTM Coordinates (x, y): ' + str(xutm) + ', ' + str(yutm)
	
    #insertPointOfInterest(xutm, yutm)
	
def geocode(address):
    global poiName
    poiName = address
    params = {
        'address': address,
        'sensor': 'false'
	}

    url = googleGeocodeUrl + urllib.urlencode(params)
    print url
    response = urllib.urlopen(url)
    jsonResponse = json.load(response)
	
    coords = []
    if (len(jsonResponse['results']) > 0):
        for location in jsonResponse['results'][0]['geometry']['location'].items():
	        coords.append(location[1])
    else:
        coords.append(40)
        coords.append(8)
	
    print 'Point Of Interest: ' + poiName
    print 'Latitude - Longitude: ' + str(coords[0]) + ', ' + str(coords[1])
    
    getUTMCoordinatesFromJS(coords[0], coords[1])
    
def main():
    connectToDB()
	
    pointsOfInterest = list()    
    with open('POI.txt') as file:
	    pointsOfInterest = file.readlines()
    
    for point in pointsOfInterest:
        coordinates = geocode(point)

    #insertUsers()
	
    closeDBConnection()
		
def readAddressParameter():
    if 1 < len(sys.argv):
        address = ' '.join(sys.argv[1 : len(sys.argv)])
    else:
        address = '1600 Amphitheatre Parkway, Mountain View, CA 94043, USA'
	
if __name__ ==  '__main__':
    main()
