//For RTLD_NEXT define _GNU_SOURCE in cmdline for compilation
#define _GNU_SOURCE

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>

typedef void * (*malloc_like_func)(size_t);
typedef void (*free_like_func)(void *);

static malloc_like_func sysmalloc = NULL;
static free_like_func sysfree = NULL;
static FILE *fp;
static char * logFileName = "allocation.txt";
static bool initComplete = false;

__attribute__((constructor)) void Init(void) 
{

  // initialization code
  if (!initComplete)
  {
	//Do this at the beginning as this calls malloc
	dlerror(); // clear any previous error
	sysmalloc = (malloc_like_func) dlsym(RTLD_NEXT, "malloc");
	char * error = dlerror();	
	if (error)
	{
   		exit(1);
	}

	sysfree = (free_like_func) dlsym(RTLD_NEXT, "free");
	error = dlerror();	
	if (error)
	{
		exit(1);
	}

	initComplete = true;
	//Note: fopen will call malloc
	fp = fopen(logFileName, "w");
	//Turn off IO bufferring to prevent malloc calls in fprintf()
	setbuf(fp, NULL);
  }
}

__attribute__((destructor)) void Deinit(void) 
{
  // De-initialization code
  if (fp != NULL)
  {
  	fclose(fp);
  }
}

void * malloc(size_t size)
{
	void *retPtr = sysmalloc(size);
	if (fp != NULL)
	{
		fprintf(fp, "M %lu %lu \n", (uintptr_t)retPtr, size);
	}
	return retPtr;
}

void free(void * ptr)
{
	if (fp != NULL)
	{
		fprintf(fp, "F %lu \n", (uintptr_t)ptr);
	}
	return sysfree(ptr);
}
