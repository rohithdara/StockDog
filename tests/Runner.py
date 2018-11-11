import sys
from unittest import TestLoader, TestSuite, TextTestRunner

from authTests.PostUserTests import PostUserTests
from routesTests.ChartsTests import ChartsTests


if __name__ == '__main__':
   loader = TestLoader()
   suite = TestSuite(
      (
         loader.loadTestsFromTestCase(PostUserTests),
         loader.loadTestsFromTestCase(ChartsTests)
      )
   )

   runner = TextTestRunner()
   result = runner.run(suite)
   sys.exit(not result.wasSuccessful())
