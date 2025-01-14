#!/bin/sh
gcc -fPIC -c allocator.c -o allocator.o
gcc -shared -o myalloc.so allocator.o -ldl
#Test application for wrapper
gcc main.c
#Note Invoke your app using LD_PRELOAD as shown below
LD_PRELOAD=./myalloc.so ./a.out

