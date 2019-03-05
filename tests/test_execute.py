from jupyter_runner.execute import get_tasks

def test_get_tasks():

    kw_tasks = get_tasks(
        parameter_file=None,
        notebooks=['A.ipynb'],
        output_dir='/xxx',
        debug=False,
        overwrite=True,
        output_format='html',
        timeout=-1,
        allow_errors=True,
        hide_input=True,
    )

    assert kw_tasks == [
        {
            'allow_errors': True,
            'hide_input': True,
            'notebook': 'A.ipynb',
            'output_format': 'html',
            'debug': False,
            'parameters': {},
            'output_file': '/xxx/A.html',
            'timeout': -1,
            'overwrite': True,
        },
    ]
