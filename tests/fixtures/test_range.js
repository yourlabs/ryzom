function func() {
    var a = [...Array(10).keys()];
    for (const x of [...Array(3).keys()]) {
        console.log(x);
    }
}
