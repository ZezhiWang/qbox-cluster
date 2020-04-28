// Copyright 2017 Istio Authors
//
// Licensed under the Apache License, Version 2.0 (the "License")
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http: // www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

var http = require('http')
var dispatcher = require('httpdispatcher')
var faker = require('faker')

var port = parseInt(process.argv[2])

var local_log = {}

dispatcher.onGet(/^\/add\/[0-9]*/, function(req, res) {

    var id = req.url.split('/').pop()
    id = parseInt(id)
    fake_data = faker.random.number()

    local_log[id] = fake_data

    res.writeHead(200, {'Content-type': 'application/json'})
    res.end(JSON.stringify(local_log))
})
dispatcher.onGet(/^\/delete\/[0-9]*/, function(req, res) {

    var id = req.url.split('/').pop()
    id = parseInt(id)

    if(id in local_log) {
        delete local_log[id]
    }

    res.writeHead(200, {'Content-type': 'application/json'})
    res.end(JSON.stringify(local_log))
})
dispatcher.onGet(/^\/saga-add\/[0-9]*/, function(req, res) {


    var id = req.url.split('/').pop()
    id = parseInt(id)
    var options = {
        host: 'localhost',
        port: 3001,
        path: '/add/',
        method: 'GET',
        headers: { 'Start-Faking': 'True', 'Product-ID': id}
    };
    fake_data = faker.random.number()
    local_log[id] = fake_data

    const request = http.request(options, (result) => {
        if (result.statusCode != 200) { delete local_log[id] }
        res.writeHead(result.statusCode, { 'Content-type': 'application/json' })
        res.end(JSON.stringify(local_log))
        result.on('end', () => {
        });
    });
    request.end()
})
dispatcher.onGet(/^\/saga-delete\/[0-9]*/, function(req, res) {

    var id = req.url.split('/').pop()
    id = parseInt(id)
    var options = {
        host: 'localhost',
        port: 3001,
        path: '/delete/',
        method: 'GET',
        headers: { 'Start-Faking': 'True', 'Product-ID': id }
    };
    if(id in local_log) {
        delete local_log[id]
    }

    const request = http.request(options, (result) => {
        if (result.statusCode != 200) { delete local_log[id] }
        res.writeHead(result.statusCode, { 'Content-type': 'application/json' })
        res.end(JSON.stringify(local_log))
        result.on('end', () => {
        });
    });
    request.end()
})

dispatcher.onGet(/^\/list/, function (req, res) {
    res.writeHead(200, { 'Content-type': 'application/json' })
    res.end(JSON.stringify(local_log))
})

function handleRequest(request, response) { 
    try {
        console.log(request.method + ' ' + request.url)
        dispatcher.dispatch(request, response)
    } catch(err) {
        console.log(err)
    }
}

var server = http.createServer(handleRequest)

server.listen(port, function() {
    console.log('Server listening on: http://0.0.0.0:%s', port)
})
