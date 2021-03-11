var DIR = "../static/img/router.png";
var EDGE_LENGTH_MAIN = 200;
var EDGE_LENGTH_SUB = 150;

// create an array with nodes
var nodesArray = [];

for (var i = 1; i <= 26; i++) {
    nodesArray.push({
        id: i,
        image: DIR,
        imagePadding: {
            bottom: -25
        },
        size: 45,
        scaling: {
            label: true
        },
        opacity: 1,
        shape: 'image',
        label: 'dpid: ' + i
    });

}

// create an array with edges
// var edgesArray = [
//     { from: 1, to: 2, length: EDGE_LENGTH_MAIN, width: 4.5, color: "#e60000" },
//     { from: 1, to: 3, length: EDGE_LENGTH_SUB, width: 3, color: "#ff6600" },
//     { from: 1, to: 4, length: EDGE_LENGTH_SUB, width: 3, color: "#ff6600" },
//     { from: 2, to: 5, length: EDGE_LENGTH_SUB, width: 3, color: "#ff6600" },
//     { from: 2, to: 6, length: EDGE_LENGTH_SUB, width: 3, color: "#ff6600" },
//     { from: 3, to: 7, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 3, to: 8, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 4, to: 7, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 4, to: 8, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 5, to: 9, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 5, to: 10, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 6, to: 9, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" },
//     { from: 6, to: 10, length: EDGE_LENGTH_SUB, width: 1.5, color: "#33cc33" }
// ];

var edgesArray = [
    {from: 1, to: 2},
    {from: 1, to: 19},
    {from: 2, to: 19},
    {from: 1, to: 3},
    {from: 1, to: 4},
    {from: 1, to: 5},
    {from: 1, to: 6},
    {from: 1, to: 7},
    {from: 2, to: 8},
    {from: 2, to: 9},
    {from: 2, to: 10},
    {from: 2, to: 11},
    {from: 2, to: 12},
    {from: 3, to: 14},
    {from: 3, to: 22},
    {from: 4, to: 17},
    {from: 4, to: 20},
    {from: 4, to: 23},
    {from: 5, to: 18},
    {from: 5, to: 24},
    {from: 6, to: 13},
    {from: 6, to: 15},
    {from: 6, to: 21},
    {from: 6, to: 25},
    {from: 7, to: 16},
    {from: 7, to: 26},
    {from: 8, to: 14},
    {from: 8, to: 22},
    {from: 9, to: 17},
    {from: 9, to: 23},
    {from: 10, to: 18},
    {from: 10, to: 24},
    {from: 11, to: 13},
    {from: 11, to: 15},
    {from: 11, to: 25},
    {from: 12, to: 16},
    {from: 12, to: 26},
    {from: 13, to: 14},
    {from: 15, to: 16},
    {from: 17, to: 18},
    {from: 19, to: 20},
    {from: 21, to: 22},
    {from: 23, to: 24},
    {from: 25, to: 26}
]

// create a network
var container = document.getElementById('mynetwork');

var nodes = new vis.DataSet(nodesArray)
var edges = new vis.DataSet(edgesArray)

// provide the data in the vis format
var data = {
    nodes: nodes,
    edges: edges
};
var options = {
    autoResize: true,
    interaction: {
        zoomView: false
    },
    layout: {
        hierachical: true
    }
};

// initialize your network!
var network = new vis.Network(container, data, options);

network.on("click", function (params) {
    $("#statusTable tbody tr").remove();
    var edgeIds = params.edges;
    for (var edgeId of edgeIds) {
        var from = edges.get(edgeId).from.toString().padStart(16, "0");
        var to = edges.get(edgeId).to.toString().padStart(16, "0");
        addRow(from, to);
        addRow(to, from);
    };
});

function addRow(from, to) {
    $.getJSON('/mydb/links_bw/last/' + from + '/' + to, function (data) {
        var bw = data.last;
        var src_dpid = data.src_dpid;
        var dst_dpid = data.dst_dpid;
        var src_port = data.src_port;
        var dst_port = data.dst_port;
        $('#statusTable').find('tbody').append('<tr>' +
            '<td>' + src_dpid + '</td>' +
            '<td>' + src_port + '</td>' +
            '<td>' + dst_dpid + '</td>' +
            '<td>' + dst_port + '</td>' +
            '<td>' + bw + '</td>' +
            '</tr>');
    });
}