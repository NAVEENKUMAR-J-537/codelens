import ast


def analyze_python_file(file_path):

    results = {
        "lines": 0,
        "functions": 0,
        "methods": 0,
        "async_functions": 0,
        "async_methods": 0,
        "classes": 0,
        "imports": 0,
        "decorators": 0,
        "issues": []
    }

    try:

        # -----------------------------------
        # READ SOURCE CODE
        # -----------------------------------

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            source_code = file.read()


        results["lines"] = len(
            source_code.splitlines()
        )


        tree = ast.parse(source_code)


        # -----------------------------------
        # TRACK IMPORTS AND USED NAMES
        # -----------------------------------

        imported_names = []

        used_names = set()


        # -----------------------------------
        # FIND CLASS METHODS
        # -----------------------------------

        method_nodes = set()


        for node in ast.walk(tree):

            if isinstance(
                node,
                ast.ClassDef
            ):

                results["classes"] += 1

                results["decorators"] += len(
                    node.decorator_list
                )


                for child in node.body:

                    if isinstance(
                        child,
                        (
                            ast.FunctionDef,
                            ast.AsyncFunctionDef
                        )
                    ):

                        method_nodes.add(
                            child
                        )


        # -----------------------------------
        # ANALYZE ALL NODES
        # -----------------------------------

        for node in ast.walk(tree):


            # ===================================
            # NORMAL FUNCTION / METHOD
            # ===================================

            if isinstance(
                node,
                ast.FunctionDef
            ):

                if node in method_nodes:

                    results["methods"] += 1

                else:

                    results["functions"] += 1


                results["decorators"] += len(
                    node.decorator_list
                )


                detect_function_issues(
                    node,
                    results
                )


            # ===================================
            # ASYNC FUNCTION / METHOD
            # ===================================

            elif isinstance(
                node,
                ast.AsyncFunctionDef
            ):

                if node in method_nodes:

                    results["async_methods"] += 1

                else:

                    results["async_functions"] += 1


                results["decorators"] += len(
                    node.decorator_list
                )


                detect_function_issues(
                    node,
                    results
                )


            # ===================================
            # NORMAL IMPORT
            # ===================================

            elif isinstance(
                node,
                ast.Import
            ):

                results["imports"] += 1


                for alias in node.names:

                    if alias.asname:

                        used_name = (
                            alias.asname
                        )

                    else:

                        used_name = (
                            alias.name
                            .split(".")[0]
                        )


                    imported_names.append({
                        "name": alias.name,
                        "used_name": used_name,
                        "line": node.lineno
                    })


            # ===================================
            # FROM IMPORT
            # ===================================

            elif isinstance(
                node,
                ast.ImportFrom
            ):

                results["imports"] += 1


                for alias in node.names:

                    if alias.name == "*":
                        continue


                    if alias.asname:

                        used_name = (
                            alias.asname
                        )

                    else:

                        used_name = (
                            alias.name
                        )


                    if node.module:

                        display_name = (
                            f"{node.module}."
                            f"{alias.name}"
                        )

                    else:

                        display_name = (
                            alias.name
                        )


                    imported_names.append({
                        "name": display_name,
                        "used_name": used_name,
                        "line": node.lineno
                    })


            # ===================================
            # USED NAMES
            # ===================================

            elif isinstance(
                node,
                ast.Name
            ):

                if isinstance(
                    node.ctx,
                    ast.Load
                ):

                    used_names.add(
                        node.id
                    )


            # ===================================
            # BARE EXCEPT
            # ===================================

            elif isinstance(
                node,
                ast.ExceptHandler
            ):

                if node.type is None:

                    results["issues"].append({
                        "type": "Bare Except",
                        "line": node.lineno,
                        "message": (
                            "Avoid using a bare "
                            "except block."
                        )
                    })


            # ===================================
            # FUNCTION CALLS
            # ===================================

            elif isinstance(
                node,
                ast.Call
            ):

                detect_security_issues(
                    node,
                    results
                )


        # -----------------------------------
        # DETECT UNUSED IMPORTS
        # -----------------------------------

        for imported in imported_names:

            if (
                imported["used_name"]
                not in used_names
            ):

                results["issues"].append({
                    "type": "Unused Import",
                    "line": imported["line"],
                    "message": (
                        f"Import "
                        f"'{imported['name']}' "
                        "is never used."
                    )
                })


        return results


    except (
        SyntaxError,
        UnicodeDecodeError,
        OSError
    ):

        return results



# ===========================================
# FUNCTION QUALITY CHECKS
# ===========================================

def detect_function_issues(
    node,
    results
):

    # -----------------------------------
    # EMPTY FUNCTION
    # -----------------------------------

    if (
        len(node.body) == 1
        and isinstance(
            node.body[0],
            ast.Pass
        )
    ):

        results["issues"].append({
            "type": "Empty Function",
            "line": node.lineno,
            "function": node.name,
            "message": (
                f"Function '{node.name}' "
                "contains only pass."
            )
        })


    # -----------------------------------
    # MUTABLE DEFAULT ARGUMENT
    # -----------------------------------

    defaults = (
        node.args.defaults
        + node.args.kw_defaults
    )


    for default in defaults:

        if isinstance(
            default,
            (
                ast.List,
                ast.Dict,
                ast.Set
            )
        ):

            results["issues"].append({
                "type": (
                    "Mutable Default Argument"
                ),
                "line": node.lineno,
                "function": node.name,
                "message": (
                    f"Function '{node.name}' "
                    "uses a mutable default "
                    "argument."
                )
            })


    # -----------------------------------
    # LONG FUNCTION
    # -----------------------------------

    if hasattr(
        node,
        "end_lineno"
    ):

        function_length = (
            node.end_lineno
            - node.lineno
            + 1
        )


        if function_length > 50:

            results["issues"].append({
                "type": "Long Function",
                "line": node.lineno,
                "function": node.name,
                "message": (
                    f"Function '{node.name}' "
                    f"is {function_length} "
                    "lines long."
                )
            })



# ===========================================
# SECURITY CHECKS
# ===========================================

def detect_security_issues(
    node,
    results
):

    # -----------------------------------
    # EVAL()
    # -----------------------------------

    if (
        isinstance(
            node.func,
            ast.Name
        )
        and node.func.id == "eval"
    ):

        results["issues"].append({
            "type": (
                "Potential Security Risk"
            ),
            "line": node.lineno,
            "message": (
                "Use of eval() detected. "
                "eval() executes dynamic "
                "Python code and can be "
                "dangerous with untrusted input."
            )
        })


    # -----------------------------------
    # EXEC()
    # -----------------------------------

    if (
        isinstance(
            node.func,
            ast.Name
        )
        and node.func.id == "exec"
    ):

        results["issues"].append({
            "type": (
                "Potential Security Risk"
            ),
            "line": node.lineno,
            "message": (
                "Use of exec() detected. "
                "exec() executes dynamic "
                "Python code and can be "
                "dangerous with untrusted input."
            )
        })


    # -----------------------------------
    # SUBPROCESS WITH shell=True
    # -----------------------------------

    if is_subprocess_call(node):

        for keyword in node.keywords:

            if (
                keyword.arg == "shell"
                and isinstance(
                    keyword.value,
                    ast.Constant
                )
                and keyword.value.value
                is True
            ):

                results["issues"].append({
                    "type": (
                        "Potential Security Risk"
                    ),
                    "line": node.lineno,
                    "message": (
                        "Subprocess call with "
                        "shell=True detected. "
                        "This may create a shell "
                        "injection risk when "
                        "untrusted input is used."
                    )
                })

                break



def is_subprocess_call(node):
    """
    Detect calls such as:

    subprocess.run(...)
    subprocess.call(...)
    subprocess.Popen(...)
    """

    if not isinstance(
        node.func,
        ast.Attribute
    ):

        return False


    if not isinstance(
        node.func.value,
        ast.Name
    ):

        return False


    if (
        node.func.value.id
        != "subprocess"
    ):

        return False


    subprocess_functions = {
        "run",
        "call",
        "check_call",
        "check_output",
        "Popen"
    }


    return (
        node.func.attr
        in subprocess_functions
    )