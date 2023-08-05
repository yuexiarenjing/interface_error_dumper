#! /bin/bash

if [ ! -z "$1" ]
then
    if [ $1 == clean ]
    then
        echo remove build folder...
        rm -rf *.o  BigLakes1024.out rivers1.out
        find . \( -name \*.o -o -name '*.fppized.f*' -o -name '*.i' -o -name '*.mod' \) -print | xargs rm -rf
        rm -rf astar
        rm -rf astar.exe
        rm -rf core
        rm -rf 
        exit 0
    fi
fi

/usr/bin/g++ -c -g -o CreateWay_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       CreateWay_.cpp
/usr/bin/g++ -c -g -o Places_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       Places_.cpp
/usr/bin/g++ -c -g -o RegBounds_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       RegBounds_.cpp
/usr/bin/g++ -c -g -o RegMng_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       RegMng_.cpp
/usr/bin/g++ -c -g -o Way2_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       Way2_.cpp
/usr/bin/g++ -c -g -o WayInit_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       WayInit_.cpp
/usr/bin/g++ -c -g -o Library.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       Library.cpp
/usr/bin/g++ -c -g -o Random.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       Random.cpp
/usr/bin/g++ -c -g -o Region_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       Region_.cpp
/usr/bin/g++ -c -g -o RegWay_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       RegWay_.cpp
/usr/bin/g++ -c -g -o Way_.o -DSPEC_CPU -DNDEBUG -DSPEC_CPU_LITTLE_ENDIAN   -fno-strict-aliasing   -DSPEC_CPU_LP64       Way_.cpp
/usr/bin/g++ -g -fno-strict-aliasing  -DSPEC_CPU_LP64        CreateWay_.o Places_.o RegBounds_.o RegMng_.o Way2_.o WayInit_.o Library.o Random.o Region_.o RegWay_.o Way_.o                     -o astar
