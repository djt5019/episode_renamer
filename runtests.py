import EpParser.tests

import unittest

def main():
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule( EpParser.tests )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run( suite )
    
    

if __name__ == '__main__':
    main()