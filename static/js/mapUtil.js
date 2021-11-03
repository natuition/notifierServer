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
                    /* other */ 'darkblue'
                    ]
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
    });
   
    map.getSource('points').setData({
        'type': 'FeatureCollection',
        'features': points
    });

    if(!zoomOn){
        map.panTo(points[points.length - 1]['geometry']['coordinates']);
        zoomOn = true;
    }
});