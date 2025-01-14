#include <stdio.h>
#include <stdlib.h>


int main(void)
{
	for (int i = 0; i < 10; i++)
	{
		int *array = (int * )malloc(10 * i * sizeof(int));
		if (array != NULL)
		{
			array[0] = 1;
			free(array);
		}
	}
	return 0;
}