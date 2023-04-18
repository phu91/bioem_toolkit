#include <stdio.h>
//#include <iostream>
#include <string.h>
#include <stdlib.h>
//#include <algorithm>
//#include <fstream>

//using namespace std;

float * q_mult(float q1[4],float q2[4]) {
	float x1,x2,y1,y2,z1,z2,w1,w2;
	float x,y,z,w;
	static float q[4];
	x1=q1[0]; y1=q1[1]; z1=q1[2]; w1=q1[3];
        x2=q2[0]; y2=q2[1]; z2=q2[2]; w2=q2[3];
	w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2;
    	x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2;
   	y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2;
    	z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2;
	q[0]=x; q[1]=y;q[2]=z;q[3]=w;
	return q;
};

void main(int argc, char *argv[] ) {
	float q1[4];
        float q2[4];
	float *q;
	int gridpoints;	
	FILE *out,*base,*grid;
	int i,j;
	char gridFilename[20];
	
	base=fopen(argv[1],"r");
        out=fopen(argv[2],"w");
	gridpoints=atoi(argv[3]);
	sprintf(gridFilename,"smallGrid_%d",gridpoints);
	grid=fopen(gridFilename,"r");


	int bufferLength = 255;
	char buffer[bufferLength]; 

	int n=0;
	while(fgets(buffer, bufferLength, base)) 
	{
		sscanf(buffer,"%f %f %f %f",&q1[0],&q1[1],&q1[2],&q1[3]);
		while(fgets(buffer, bufferLength,grid ) ) 
			{
		                sscanf(buffer,"%f %f %f %f",&q2[0],&q2[1],&q2[2],&q2[3]);
			        q=q_mult(q1,q2);	

				for ( i = 0; i < 4; i++ )
				{
					//fprintf(out,"%f\t", q2[i]);
					fprintf(out,"%f\t", *(q+i));		
				}
				fprintf(out,"\n");
			}
	//	printf(buffer);	
		rewind(grid);
	}
	fclose(out);
	fclose(base);
	fclose(grid);
	
//	return 0;
}


