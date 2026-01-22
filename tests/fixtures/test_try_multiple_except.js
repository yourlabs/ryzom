function func() {
    try {
        do_something();
    } catch (__dummy0__) {
        if (__dummy0__ instanceof py_builtins.TypeError) {
            handle_type_error();
        } else if (__dummy0__ instanceof py_builtins.ValueError) {
            handle_value_error();
        } else {
            throw __dummy0__;
        }
    }
}
