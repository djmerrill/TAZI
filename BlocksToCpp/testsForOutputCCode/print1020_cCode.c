#include <iostream>
#include <cmath>
#include <stdlib.h>
using namespace std;
int main() {
   int item = 1;
  for(int i = 1; i<=(10); i+=(1)) {
    int item = i * 2;
    if((int)item % (int)10 == 0) {
      cout << (item) << endl;
    };
   };
   return 0;
}
