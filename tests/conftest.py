"""Select an OCR backend explicitly for integration runs, and keep tests off the network."""
import os

os.environ.setdefault('RESHOOT_OFFLINE', '1')  # doctor would otherwise ask PyPI for the latest release


def pytest_addoption(parser):
    parser.addoption('--ocr-backend', choices=['auto', 'vision', 'tesseract'], default=None,
                     help='explicit OCR backend for scanner integration tests')


def pytest_configure(config):
    config._reshoot_previous_ocr = os.environ.get('RESHOOT_OCR')
    selected = config.getoption('--ocr-backend')
    if selected:
        os.environ['RESHOOT_OCR'] = selected


def pytest_unconfigure(config):
    previous = getattr(config, '_reshoot_previous_ocr', None)
    if previous is None:
        os.environ.pop('RESHOOT_OCR', None)
    else:
        os.environ['RESHOOT_OCR'] = previous
