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

function parse(str) {
    var args = [].slice.call(arguments, 1),
        i = 0;

    return str.replace(/%s/g, () => (args[i++]));
}

function log_message(value) {
    var time = process.hrtime()
    console.log(parse("[%s] %s", JSON.stringify(time[0] * 1000000 + time[1] / 1000), JSON.stringify(value)))
}

function add_id(id) {
    if (!(id in local_log)) {
        fake_data = faker.random.number()
        local_log[id] = fake_data   
    }  
}

function delete_id(id) {
    if(id in local_log) {
        delete local_log[id]
    }
}

dispatcher.onGet(/^\/add\/[0-9]*/, function(req, res) {

    var id = req.url.split('/').pop()
    id = parseInt(id)

    log_message({"id": id, "process": process.env.NAME, "action": "Received add request"})

    add_id(id)

    log_message({"id": id, "process": process.env.NAME, "action": "Completed add request"})

    res.writeHead(200, {'Content-type': 'application/json'})
    res.end(JSON.stringify(local_log))
})

dispatcher.onGet(/^\/delete\/[0-9]*/, function(req, res) {

    var id = req.url.split('/').pop()
    id = parseInt(id)

    log_message({"id": id, "process": process.env.NAME, "action": "Received delete request"})
    delete_id(id)
    log_message({"id": id, "process": process.env.NAME, "action": "Completed delete request"})

    res.writeHead(200, {'Content-type': 'application/json'})
    res.end(JSON.stringify(local_log))
})

dispatcher.onGet(/^\/saga-add\/[0-9]*/, function(req, res) {


    var id = req.url.split('/').pop()
    id = parseInt(id)
    log_message({"id": id, "process": process.env.NAME, "action": "Received saga-add request"})

    var options = {
        host: 'localhost',
        port: 3001,
        path: '/add/',
        method: 'GET',
        headers: { 'Start-Faking': 'True', 'Product-ID': id}
    };

    log_message({"id": id, "process": process.env.NAME, "action": "Adding saga-add request locally"})
    add_id(id)
    log_message({"id": id, "process": process.env.NAME, "action": "Added saga-add request locally"})

    log_message({"id": id, "process": process.env.NAME, "action": "Issuing saga-add request to children"})
    const request = http.request(options, (result) => {
        log_message({"id": id, "process": process.env.NAME, "action": "Issued saga-add request to all children"})
        if (result.statusCode != 200) { 
            log_message({"id": id, "process": process.env.NAME, "action": "Received failure from saga"})
            delete_id(id) 
            log_message({"id": id, "process": process.env.NAME, "action": "Deleted saga-add value locally"})
        }
        res.writeHead(result.statusCode, { 'Content-type': 'application/json' })
        res.end(JSON.stringify(local_log))
        result.on('end', () => {
            log_message({"id": id, "process": process.env.NAME, "action": "Finished reading saga response from qbox completely"})
        });
    });
    request.end()
})

dispatcher.onGet(/^\/saga-delete\/[0-9]*/, function(req, res) {

    var id = req.url.split('/').pop()
    id = parseInt(id)
    log_message({"id": id, "process": process.env.NAME, "action": "Received saga-delete request"})
    var options = {
        host: 'localhost',
        port: 3001,
        path: '/delete/',
        method: 'GET',
        headers: { 'Start-Faking': 'True', 'Product-ID': id }
    };

    log_message({"id": id, "process": process.env.NAME, "action": "Deleted saga-delete request locally"})
    delete_id(id)
    log_message({"id": id, "process": process.env.NAME, "action": "Deleted saga-delete request locally"})


    log_message({"id": id, "process": process.env.NAME, "action": "Issuing saga-delete request to children"})
    const request = http.request(options, (result) => {
        log_message({"id": id, "process": process.env.NAME, "action": "Issued saga-delete request to all children"})
        if (result.statusCode != 200) { 
            log_message({"id": id, "process": process.env.NAME, "action": "Received failure from saga on saga-delete"})
            add_id(id) 
            log_message({"id": id, "process": process.env.NAME, "action": "Restored saga-delete value locally"})
        }
        res.writeHead(result.statusCode, { 'Content-type': 'application/json' })
        res.end(JSON.stringify(local_log))
        result.on('end', () => {
            log_message({"id": id, "process": process.env.NAME, "action": "Finished saga-delete reading saga response from qbox completely"})
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
