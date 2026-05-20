function func() {
    var a = [{
        'b': 1,
        'c': 2
    }, {
        'b': 3,
        'c': 4
    }, {
        'b': 5,
        'c': 6
    }];
    var b = [...(function* f() { for (const x of a) { yield x['b'] } })()];
    var c = [...(function* f() { for (const x of a) { yield x.b.toString() } })()];
    console.log(b);
    console.log(c);
}
