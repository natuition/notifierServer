var socketMap = io.connect('http://' + document.domain + ':' + location.port + '/map');
    
var map;
var zoomOn = false;

document.addEventListener("DOMContentLoaded",createMap());

function createMap(){

    mapboxgl.accessToken = 'pk.eyJ1IjoidmluY2VudGxiIiwiYSI6ImNrY2F2YTA5NjF5c3kzMG8wbG5zbjk5cjcifQ.p9V3BtVZngNW1L8MRoALaw';
    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/satellite-v9',
        zoom: 18
    });

    var draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
            point: true, 
            line_string: true,
            polygon: true,
            trash: true
        },
        defaultMode: 'draw_polygon'
    })

    map.addControl(new mapboxgl.NavigationControl());
    map.addControl(draw);

    map.on('draw.create', updateArea);
    map.on('draw.update', updateArea);
    map.on('draw.delete', deleteArea);
    
    function updateArea(e) {
        var data = draw.getAll();
        var answer = document.getElementById('calculated-area');
        if (data.features.length > 0) {
            var res;
            var unit;
            if(data.features[0].geometry.type=="LineString"){
                res = turf.length(data)*1000;
                unit = " m";
            }else if(data.features[0].geometry.type=="Point"){
                res = data.features[0].geometry.coordinates
                unit = " (long, lat)"
            }else{
                var area = turf.area(data);
                res = Math.round(area * 100) / 100;
                unit = " m<sup>2</sup>";
            }
            answer.innerHTML = "Résultat : " + res + unit;
            answer.setAttribute('style','padding: 10px;');
            
        }
    }

    function deleteArea(e) {
        var answer = document.getElementById('calculated-area');
        answer.innerHTML = "";
        answer.removeAttribute('style');
    }

    map.on('load', function () {
        //Field zone
        map.addSource('field', {
            'type': 'geojson',
            'data': {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        coords_field
                    ]
                }
            }
        }); 
        map.addLayer({
            'id': 'fieldLayer',
            'type': 'fill',
            'source': 'field',
            'layout': {},
            'paint': {
                'fill-color': '#0620FB',
                'fill-opacity': 0.4
            }
        });

        coords_field.push(coords_field.at(0))

        //Field line
        map.addSource('field_corner', {
            'type': 'geojson',
            'data': {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coords_field
                }
            }
        });    
        map.addLayer({
            'id': 'field_cornerLayer',
            'type': 'line',
            'source': 'field_corner',
            'layout': {
                'line-join': 'round',
                'line-cap': 'round',
            },
            'paint': {
                'line-color': '#0620FB',
                'line-width': 4
            }
        });
        //Path point robot
        map.addSource('points', {
            'type': 'geojson',
            'data': {
                'type': 'FeatureCollection',
                'features': [
                    {'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': []
                        }
                    },
                ] 
            }
        });
        map.addLayer({
            'id': 'pointsLayer',
            'type': 'circle',
            'source': 'points',
            'paint': {
                'circle-radius': 4,
                'circle-color': [
                    'match',
                    ['get', 'Type'],
                    'Dandellion',
                    '#F7B500', // yellow
                    'Plantain_great',
                    '#22780F', // green
                    'Plantain_narrowleaf',
                    '#01D758', // light green
                    'Daisy',
                    '#3BA3BC', // cyan
                    'Mallow',
                    '#800080', // purple
                    /* other */ 'red'
                    ]
            }
        });
        //Path line robot
        map.addSource('pathRobot', {
            'type': 'geojson',
            'data': {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': []
                }
            }
        });
        map.addLayer({
            'id': 'pathRobotLayer',
            'type': 'line',
            'source': 'pathRobot',
            'layout': {
                'line-join': 'round',
                'line-cap': 'round',
            },
            'paint': {
                'line-color': 'red',
                'line-width': 2
            }
        });

        var v=decodeURI(window.location.href).split('map/')[1];
        socketMap.emit('data', {'sn': v.split("/")[0], 'session': (v.split("/")[1])});
        var reloaderData = setInterval(()=>{
            socketMap.emit('data', {'sn': v.split("/")[0], 'session': (v.split("/")[1])});
        },1000);
    });
    

}

socketMap.on('updatePoints', function(dataServ) {
    var points = [];
    var coordsPoints=[];
    dataServ.forEach((coordAndExt) => {
        coord = coordAndExt[0];
        ext = coordAndExt[1];
        if(ext === null){
            points.push({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [coord[1],coord[0]]
                }
            });
        }
        else{
            points.push({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [coord[1],coord[0]]
                },
                "properties": Object.assign({}, {'Type':Object.keys(ext)[0]}, ext)
            });
        }
        coordsPoints.push([coord[1],coord[0]]);
    });

    console.log(coordsPoints);
   
    map.getSource('points').setData({
        'type': 'FeatureCollection',
        'features': points
    });

    map.getSource('pathRobot').setData({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': coordsPoints
        }
    });

    if(!zoomOn){
        map.panTo(points[points.length - 1]['geometry']['coordinates']);
        zoomOn = true;
    }
});