async function func() {
    var res = await fetch(params).then(
        (r) => {return r}
    ).then(
        (r) => {return (console.log(r) && r.status)}
    );
};
