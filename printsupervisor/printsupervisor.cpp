 #include <stdio.h>
 #include <stdlib.h>
 #include <string.h>
 #include <memory.h>
 
 //new
 #include <cv.h>
 #include <highgui.h> 
 #include "time.h"
 
 #include <thread>
 #include <mutex>
 #include <chrono>
 #include <zmq.hpp>
 
 
 // OPENCV
 #include <iostream>
 #include <fstream>
 #include <sstream>
 #include "time.h"
 
 #include "opencv2/core/core.hpp"
 #include "opencv2/contrib/contrib.hpp"
 #include "opencv2/highgui/highgui.hpp"
 #include "opencv2/imgproc/imgproc.hpp"
 #include "opencv2/objdetect/objdetect.hpp"
 
 using namespace cv;
 using namespace std;
 
 //------------------------ Detection code -------------------------------
 
 
 
 
 const float pi = 3.14159265f;
 int time1=0, time2=0, airprint=0, nonairprint=0;
 
 
 struct Rpoint{ 
     int dx;
     int dy;
     float phi;
 };
 
 struct Rpoint2{
     float x;
     float y;
     int phiindex;
 };
 
 class GenHoughTrnf{
     
 public:
     //last detected position of the artefact
     vector<pair <int, int> > lastDetected;
 
 private:
     // accumulator matrix
     Mat accum;
     // accumulator matrix
     Mat showimage;
     // contour points:
     std::vector<Rpoint> pts;
     // reference point (inside contour(
     Vec2i refPoint;
     // R-table of template object:
     std::vector<std::vector<Vec2i> > Rtable;
     // number of intervals for angles of R-table:
     int intervals;
     // threasholds of canny edge detector
     int thr1;
     int thr2;
     // width of template contour
     int wtemplate;
     // minimum and maximum width of scaled contour
     int wmin;
     int wmax;
     // minimum and maximum rotation allowed for template
     float phimin;
     float phimax;
     // dimension in pixels of squares in image
     int rangeXY;
     // interval to increase scale
     int rangeS;
     
 public:
     
     GenHoughTrnf(){
         // default values
         
         // canny threasholds
         thr1 = 50;
         thr2 = 150;
         
         // minimun and maximum width of the searched template
         wmin = 30;
         wmax = 50;
         // increasing step in pixels of the width
         rangeS = 5;
         // side of the squares in which the image is divided
         rangeXY = 6;
         
         // min value allowed is -pi
         phimin = -0.1;//-pi/6;
         // max value allowed is +pi
         phimax = 0.1;//+pi/6;
         // number of slices (angles) in R-table
         intervals = 16;
         
         lastDetected.clear();
     }
     
     //obsolete function: threshold for canny edge detection. Computed automatically here.
     void setTresholds(int t1, int t2){
         thr1 = t1;
         thr2 = t2;
     }
     
     //advanced option: scale range of artefact
     void setLinearPars(int w1, int w2, int rS, int rXY){
         wmin = w1;
         wmax = w2;
         rangeS = rS;
         rangeXY = rXY;
     }
     
     //advanced option: possible rotation range of artefact in radiens
     void setAngularPars(int p1, int p2, int ints){
         if (p1<p2){
             if (p1>-pi){
                 phimin = p1;    
             }
             if (p2<+pi){
                 phimax = p2;
             }
         }
         intervals = ints;
     }
     
     // save file with canny edge of the original image
     /*void createTemplate(){
         Mat input_img = imread("files/template_custome", 1);
         Mat src_gray;
         Mat detected_edges;
         src_gray.create( Size(input_img.cols, input_img.rows), CV_8UC1);
         cvtColor(input_img, src_gray, CV_BGR2GRAY); 
         blur( src_gray, detected_edges, Size(3,3) );
         Canny( detected_edges, detected_edges, 1, 100, 3 );
         imwrite("files/contour_rough.bmp", detected_edges);
     }*/
     
     void createRtable(){
         // code can be improved reading a pre-saved Rtable
         readPoints();
         readRtable();
     }
     
     // fill accumulator matrix
     void accumulate(cv::Mat& input_img)
     {
         showimage = input_img;
         // transform image to grayscale:
         Mat src_gray = input_img;
         //src_gray.create( Size(input_img.cols, input_img.rows), CV_8UC1);
         //cvtColor(input_img, src_gray, CV_BGR2GRAY); 
         // reduce noise with a kernel 3x3 and get cannyedge image:
         Mat detected_edges;
         //detected_edges = src_gray;
         blur( src_gray, detected_edges, Size(3,3) );
         //Detect the threshold for canny
         cv:Mat thres_img;
         double high_thres = cv::threshold( src_gray, thres_img, 0, 255, CV_THRESH_BINARY+CV_THRESH_OTSU ); //thresh detection
         Canny( detected_edges, detected_edges, high_thres*0.5, high_thres, 3 );
         imwrite("files/rough.bmp", detected_edges);
         imshow("detected_edges", detected_edges);
         cvWaitKey(10);
         // get Scharr matrices from image to obtain contour gradients
         Mat dx;
         dx.create( Size(input_img.cols, input_img.rows), CV_16SC1);
         Sobel(src_gray, dx, CV_16S, 1, 0, CV_SCHARR);
         Mat dy;
         dy.create( Size(input_img.cols, input_img.rows), CV_16SC1);
         Sobel(src_gray, dy, CV_16S, 0, 1, CV_SCHARR);
         // load all points from image all image contours on vector pts2
         int nl= detected_edges.rows;
         int nc= detected_edges.cols; 
         float deltaphi = pi/intervals;
         float inv_deltaphi = (float)intervals/pi;
         float inv_rangeXY = (float)1/rangeXY;
         float pi_half = pi*0.5f;
         std::vector<Rpoint2> pts2;
         for (int j=0; j<nl; ++j) {
             uchar* data= (uchar*)(detected_edges.data + detected_edges.step.p[0]*j);
             for (int i=0; i<nc; ++i) {              
                 if ( data[i]==255  ) // consider only white points (contour)
                 {
                     short vx = dx.at<short>(j,i);
                     short vy = dy.at<short>(j,i);
                     Rpoint2 rpt;
                     rpt.x = i*inv_rangeXY;
                     rpt.y = j*inv_rangeXY;
                     float a = atan2((float)vy, (float)vx);              //  gradient angle in radians
                     float phi = ((a > 0) ? a-pi_half : a+pi_half);      // contour angle with respect to x axis
                     int angleindex = (int)((phi+pi*0.5f)*inv_deltaphi); // index associated with angle (0 index = -90 degrees)
                     if (angleindex == intervals) angleindex=intervals-1;// -90�angle and +90� has same effect
                                                rpt.phiindex = angleindex;
                     pts2.push_back( rpt );
                 }
             }
         }
         // OpenCv 4-dimensional matrix definition and in general a useful way for defining multidimensional arrays and vectors in c++
         // create accumulator matrix
         int X = ceil((float)nc/rangeXY);
         int Y = ceil((float)nl/rangeXY);
         int S = ceil((float)(wmax-wmin)/rangeS+1.0f);
         int R = ceil(phimax/deltaphi)-floor(phimin/deltaphi);
         if (phimax==pi && phimin==-pi) R--;     
         int r0 = -floor(phimin/deltaphi);
         int matSizep_S[] = {X, Y, S, R};
         accum.create(4, matSizep_S, CV_16S);
         accum = Scalar::all(0);
         // icrease accum cells with hits corresponding with slope in Rtable vector rotatated and scaled
         float inv_wtemplate_rangeXY = (float)1/(wtemplate*rangeXY);
         // rotate RTable from minimum to maximum angle
         for (int r=0; r<R; ++r) {  // rotation
                        int reff = r-r0;
                        std::vector<std::vector<Vec2f> > Rtablerotated(intervals);
                        // cos and sin are computed in the outer loop to reach computational efficiency
                        float cs = cos(reff*deltaphi);
                        float sn = sin(reff*deltaphi);
                        for (std::vector<std::vector<Vec2i> >::size_type ii = 0; ii < Rtable.size(); ++ii){
                            for (std::vector<Vec2i>::size_type jj= 0; jj < Rtable[ii].size(); ++jj){
                                int iimod = (ii+reff) % intervals;
                                Rtablerotated[iimod].push_back(Vec2f(cs*Rtable[ii][jj][0] - sn*Rtable[ii][jj][1], sn*Rtable[ii][jj][0] + cs*Rtable[ii][jj][1]));
                            }
                        }
                        // scale the rotated RTable from minimum to maximum scale
                        for (int s=0; s<S; ++s) {  // scale
                                std::vector<std::vector<Vec2f> > Rtablescaled(intervals);
                                int w = wmin + s*rangeS;
                                float wratio = (float)w*inv_wtemplate_rangeXY;  
                                for (std::vector<std::vector<Vec2f> >::size_type ii = 0; ii < Rtablerotated.size(); ++ii){
                                    for (std::vector<Vec2f>::size_type jj= 0; jj < Rtablerotated[ii].size(); ++jj){
                                        Rtablescaled[ii].push_back(Vec2f(wratio*Rtablerotated[ii][jj][0], wratio*Rtablerotated[ii][jj][1]));    
                                    }
                                }
                                // iterate through each point of edges and hit corresponding cells from rotated and scaled Rtable
                                for (vector<Rpoint2>::size_type t = 0; t < pts2.size(); ++t){ // XY plane                               
                                        int angleindex = pts2[t].phiindex;
                                        for (std::vector<Vec2f>::size_type index = 0; index < Rtablescaled[angleindex].size(); ++index){
                                            float deltax = Rtablescaled[angleindex][index][0];
                                            float deltay = Rtablescaled[angleindex][index][1];                                                      
                                            int xcell = (int)(pts2[t].x + deltax);
                                            int ycell = (int)(pts2[t].y + deltay);
                                            if ( (xcell<X)&&(ycell<Y)&&(xcell>-1)&&(ycell>-1) ){
                                                //(*( (short*)(accum.data + xcell*accum.step.p[0] + ycell*accum.step.p[1] + s*accum.step.p[2]+ r*accum.step.p[3])))++;
                                                (*ptrat4D(accum, xcell, ycell, s, r))++;
                                            }
                                        }
                                }
                        }
         }
         
     }
     
     
     // show the best candidate detected on image
     void bestCandidate()
     {
         lastDetected.clear();
         
         double minval;
         double maxval;
         int id_min[4] = { 0, 0, 0, 0};
         int id_max[4] = { 0, 0, 0, 0};
         minMaxIdx(accum, &minval, &maxval, id_min, id_max);
         
         int nl= showimage.rows;
         int nc= showimage.cols; 
         Mat     input_img2 = showimage.clone();
         
         Vec2i referenceP = Vec2i(id_max[0]*rangeXY+(rangeXY+1)/2, id_max[1]*rangeXY+(rangeXY+1)/2);
         
         // rotate and scale points all at once. Then impress them on image
         std::vector<std::vector<Vec2i> > Rtablerotatedscaled(intervals);
         float deltaphi = pi/intervals;
         int r0 = -floor(phimin/deltaphi);
         int reff = id_max[3]-r0;
         float cs = cos(reff*deltaphi);
         float sn = sin(reff*deltaphi);
         int w = wmin + id_max[2]*rangeS;
         float wratio = (float)w/(wtemplate);    
         for (std::vector<std::vector<Vec2i> >::size_type ii = 0; ii < Rtable.size(); ++ii){
             for (std::vector<Vec2i>::size_type jj= 0; jj < Rtable[ii].size(); ++jj){
                 int iimod = (ii+reff) % intervals;
                 int dx = roundToInt(wratio*(cs*Rtable[ii][jj][0] - sn*Rtable[ii][jj][1]));
                 int dy = roundToInt(wratio*(sn*Rtable[ii][jj][0] + cs*Rtable[ii][jj][1]));
                 int x = referenceP[0] - dx;
                 int y = referenceP[1] - dy;
                 //Rtablerotatedscaled[ii].push_back(Vec2i( dx, dy));
                 if ( (x<nc)&&(y<nl)&&(x>-1)&&(y>-1) ){
                     //input_img2.at<Vec3b>(y, x) = Vec3b(0, 255, 255); //moving it to separate function that acepts a cv::mat and 
                     lastDetected.push_back(make_pair(x,y));
                 }
             }
         }
         
     }
     
     //checks if detected artefact candidate is in the wanted screen zone.
     bool isArtefIn(int minx, int maxx, int miny, int maxy)
     {
         for(int i=0; i<lastDetected.size(); i++)
             if( lastDetected[i].first < minx || lastDetected[i].first > maxx || lastDetected[i].second < miny || lastDetected[i].second > maxy ) return false;
             
             return true;
     }
     
     
     //draws last detected artefact
     cv::Mat drawLastDetected(cv::Mat source)
     {
         cv::Mat sourceBGR;
         cvtColor(source, sourceBGR, CV_GRAY2BGR); 
         for(int i=0; i < lastDetected.size(); i++) sourceBGR.at<Vec3b>(lastDetected[i].second, lastDetected[i].first) = Vec3b(0, 255, 255);
         
         return sourceBGR;
     }
     
     //getting the bounding box = minimom and maximum x and y coordinates
     void getBoundingBox(int &minx, int &maxx, int &miny, int &maxy) //TODO needs testing !!!
     {
         for(int i=0; i<lastDetected.size(); i++)
         {
             if(lastDetected[i].first < minx) minx = lastDetected[i].first;
             else if(lastDetected[i].first > maxx) maxx = lastDetected[i].first;
             
             if(lastDetected[i].second < miny) miny = lastDetected[i].second;
             else if(lastDetected[i].second > maxy) maxy = lastDetected[i].second;
         }
     }
     
     
 private:
     
     // load vector pts with all points from the contour
     void readPoints(){
         // read original template image and its worked-out contour
         Mat original_img = imread("files/template_star.bmp", 1);
         //imshow("original template", original_img); //test
         Mat input_img_gray;
         input_img_gray.create( Size(original_img.cols, original_img.rows), CV_8UC1);
         cvtColor(original_img, input_img_gray, CV_BGR2GRAY); 
         //Mat template_img = imread("files/contour_def.bmp", 1);
         Mat template_img = imread("files/contour_def01.bmp", 1);
         //imshow("template contour", template_img); //test
         // find reference point inside contour image and save it in variable refPoint
         int nl= template_img.rows;
         int nc= template_img.cols; 
         for (int j=0; j<nl; ++j) {
             Vec3b* data= (Vec3b*)(template_img.data + template_img.step.p[0]*j);
             for (int i=0; i<nc; ++i) {              
                 if ( data[i]==Vec3b(127,127,127)  ){
                     refPoint = Vec2i(i,j);
                 }
             }
         }
         // get Scharr matrices from original template image to obtain contour gradients
         Mat dx;
         dx.create( Size(original_img.cols, original_img.rows), CV_16SC1);
         Sobel(input_img_gray, dx, CV_16S, 1, 0, CV_SCHARR);
         Mat dy;
         dy.create( Size(original_img.cols, original_img.rows), CV_16SC1);
         Sobel(input_img_gray, dy, CV_16S, 0, 1, CV_SCHARR);
         // load points on vector
         pts.clear();
         int mindx = INT_MAX;
         int maxdx = INT_MIN;
         for (int j=0; j<nl; ++j) {
             Vec3b* data= (Vec3b*)(template_img.data + template_img.step.p[0]*j);
             for (int i=0; i<nc; ++i) {              
                 if ( data[i]==Vec3b(255,255,255)  )
                 {
                     short vx = dx.at<short>(j,i);
                     short vy = dy.at<short>(j,i);
                     Rpoint rpt;
                     //float mag = std::sqrt( float(vx*vx+vy*vy) );
                     rpt.dx = refPoint(0)-i;
                     rpt.dy = refPoint(1)-j;
                     float a = atan2((float)vy, (float)vx); //radians
                     rpt.phi = ((a > 0) ? a-pi/2 : a+pi/2);
                     //float a = atan2((float)vy, (float)vx) * 180/3.14159265358979f; //degrees
                     //rpt.phi = ((a > 0) ? a-90 : a+90);
                     // update further right and left dx
                     if (rpt.dx < mindx) mindx=rpt.dx;
                     if (rpt.dx > maxdx) maxdx=rpt.dx;
                     pts.push_back( rpt );
                 }
             }
         }
         // maximum width of the contour
         wtemplate = maxdx-mindx+1;
     }
     
     // create Rtable from contour points
     void readRtable(){
         Rtable.clear();
         Rtable.resize(intervals);
         // put points in the right interval, according to discretized angle and range size 
         float range = pi/intervals;
         for (vector<Rpoint>::size_type t = 0; t < pts.size(); ++t){
             int angleindex = (int)((pts[t].phi+pi/2)/range);
             if (angleindex == intervals) angleindex=intervals-1;
             Rtable[angleindex].push_back( Vec2i(pts[t].dx, pts[t].dy) );
         }
     }
     
     inline int roundToInt(float num) {
         return (num > 0.0) ? (int)(num + 0.5f) : (int)(num - 0.5f);
     }
     
     inline short at4D(Mat &mt, int i0, int i1, int i2, int i3){
         //(short)(mt.data + i0*mt.step.p[0] + i1*mt.step.p[1] + i2*mt.step.p[2] + i3*mt.step.p[3]);     
         return *( (short*)(mt.data + i0*mt.step.p[0] + i1*mt.step.p[1] + i2*mt.step.p[2] + i3*mt.step.p[3]));
     }
     
     inline short* ptrat4D(Mat &mt, int i0, int i1, int i2, int i3){
         return (short*)(mt.data + i0*mt.step.p[0] + i1*mt.step.p[1] + i2*mt.step.p[2] + i3*mt.step.p[3]);
     }
     
 };
 
 
 
 string command = "ok";
 string response = "none";
 mutex mut;
 
 
 
 void commandRecever() //TODO maybe implement sleep/wake thread technique rather then the banal mutex and variable one ? No time to learn that now...
 {
     // Prepare our context and socket
     zmq::context_t context (1);
     zmq::socket_t socket (context, ZMQ_REP);
     socket.bind ("tcp://*:5555");
     string com = "ok", rep = "ok";
     
     while (com != "stop") {
         zmq::message_t request;
         
         // Wait for next request from client
         socket.recv (&request);
         com = std::string(static_cast<char*>(request.data()), request.size());
         
         mut.lock();
         command = com;
         response = "ok"; //means its ok for the server to send a response
         mut.unlock();
         
         //std::this_thread::sleep_for(std::chrono::milliseconds(10)); //just in case, so as to let the main lock the mutex
         
         //cout << "[DEBUG] 01" <<endl;
         
         do
         {
             mut.lock();
             rep = response;
             mut.unlock();
             
             //std::this_thread::sleep_for(std::chrono::milliseconds(10)); //just in case, so as to let the main lock the mutex
             
             if(rep != "none" && rep != "ok") //server responded none: nothing to send to client so we only send when rep != none
             {
                 // Send reply back to client
                 //zmq::message_t reply (rep.size);
                 //memcpy ((void *) reply.data (), rep, rep.size); //TODO to send variable not a statis "something" convert to char* maybe ?
                 
                 zmq::message_t messageS(rep.size());
                 memcpy(messageS.data(), rep.data(), rep.size()); 
                 socket.send (messageS);
                 
                 cout << "[DEBUG] Reply "+rep <<endl;
             }
             
         }while(rep == "ok"); //repeat until the server has a response to the request
     }
     
     
     
     
     
     
 }
 
 int main(int argc, char** argv) //TODO all imreads out of the while loop
 { 
     //Type in the terminal: sudo uv4l --driver raspicam --auto-video_nr --width 1280 --height 720 --encoding yuv420 --bitrate 30000000
     
     VideoCapture cap(-1);
     if (!cap.isOpened())
     {
         cout << "Cannot open camera. Check if it's connected correctly or if it's not alredy in use."<< endl <<"Exiting application..." << endl;
         return -1;
     }
     cap.set(CV_CAP_PROP_FRAME_WIDTH, 1280);
     cap.set(CV_CAP_PROP_FRAME_HEIGHT, 720);
     
     string com = "ok";
     bool checkap = false;
     int viewcount=1, usrrescount=1;
     int minx=0, maxx=1200, miny=0, maxy=700; //area in which to look for the artefact
     
     //cout << "[DEBUG] 1" << endl; //test
     
     cv::FileStorage fs("usersetings.yml", cv::FileStorage::READ);
     if (fs.isOpened())
     {
            fs["minx"] >> minx;
            fs["maxx"] >> maxx;
            fs["miny"] >> miny;
            fs["maxy"] >> maxy;
            
            cout << "[DEBUG] User file: " << minx << " " << maxx << " " << miny << " " << maxy << endl; //test
     }
     else cout << "Failed to open CV FileStorage ! File might not exist..." << endl;
     fs.release(); //close the file just in case. This is done automatically on destruction of the fs object.
     
     //cout << "[DEBUG] 2" << endl; //test
     
     thread commander(commandRecever); //starts the command recever thread that will catch client commands
     
     while (com != "stop")
     {
         mut.lock();
         com = command;
         
         
         Mat frame, gray, modified;
         bool bSuccess = cap.read(frame);
         
         if (!bSuccess)
         {
             cout << "Cannot read a frame from camera" << endl;
             break;
         }
         
         //cout << "[DEBUG] 3" << endl; //test
         
         
         //imshow("Output", frame); //test
         //cvWaitKey(10); //test
         
         
         GenHoughTrnf ght; //TODO maybe put this outside of our while loop to get better speed ? Will it work ?
         
         // this is not executed when we do not wish to use detection as it takes lots of resources.
         if( (command != "printpreview")&&(command != "maketemplate")&&(command != "stopapcheck")  )
         {
             vector<Mat> channels(3);   
             split(frame, channels); // split img into YUV channels
             gray = channels[1]; //this is the grayscale channel Y. I have no idea why it's not channels[0]. 
             
             modified = imread("files/decoy.bmp",0); //size of the black screen // TODO filename ?
             cv::Rect rio0(780, 150, 150, 150); //position of the area to crop
             cv::Mat crop = gray(rio0);
             
             cv::Rect roi( cv::Point( 30, 30 ), crop.size() ); //position at the black screen
             Mat temp = modified( roi );
             crop.copyTo( temp ); //copying crop to the black screen
         }
         
         //cout << "[DEBUG] 4" << endl; //test
         
         if(command == "preview") //TODO needs testing
         {
             command = "ok";
             
             if(viewcount>49) viewcount = 1; //we want max 50 preview images saved on disc TODO make this a parametar
             else viewcount++;
             
             string staticpath = "../makerbot_tools/static/";
             string thefilename = "preview_frame_"+to_string(viewcount)+".jpg";
             
             // current date/time based on current system
             time_t now = time(0);
             string dt = ctime(&now);
             
             putText(frame, dt, cvPoint(1000,700), 
                    FONT_HERSHEY_COMPLEX_SMALL, 0.8, cvScalar(0,255,255), 1, CV_AA);
             
             imwrite(staticpath + thefilename, frame);
             
             cout << "[DEBUG] file: "+thefilename << endl; //test
             
             if(checkap)
             {
                 
                 if(airprint > 4) response = thefilename+"+ON: AIR PRINTING DETECTED !";
                 else response = thefilename+"+ON: Everythig seems fine.";
             }
             else response = thefilename+"+OFF.";
         }
         else if(command == "startapcheck")
         {
             checkap = true;
             nonairprint = 0;
             airprint = 0;
             response = "Airprint checking started...";
         }
         else if(command == "stopapcheck")
         {
             checkap = false;
             nonairprint = 0;
             airprint = 0;
             response = "Airprint checking stopped...";
         }
         else if(command == "configureartefact") //TODO needs testing
         {
             ght.createRtable();
             ght.accumulate(modified);
             ght.bestCandidate();
             
             Mat setingsimg = ght.drawLastDetected(modified);
             
             string staticpath = "../makerbot_tools/static/";
             string thefilename = "usersetresult"+to_string(usrrescount)+".jpg";
             imwrite(staticpath + thefilename, setingsimg);
             imshow("detection", setingsimg);
             
             //find bounding box
             ght.getBoundingBox(minx, maxx, miny, maxy);
             
             FileStorage fs("usersetings.yml", FileStorage::WRITE);
             fs << "minx" << minx;
             fs << "maxx" << maxx;
             fs << "miny" << miny;
             fs << "maxy" << maxy;
             fs.release();
             
             response = thefilename;
             
             if(usrrescount>5) usrrescount=1;
             else usrrescount++;
         }
         else if(command == "maketemplate") //TODO under construction ! o_O
         {
             //make new custome template
             response = "[ERROR] Not implemented yet...";
         }
         else
         {
            response = "[ERROR] Unknown command: "+command;
         }
         
         //cout << "[DEBUG] 5" << endl;
         
         if(checkap)
         {  
             ght.createRtable();
             ght.accumulate(modified);
             ght.bestCandidate();
             if(ght.isArtefIn(minx, maxx, miny, maxy)) airprint++;
             else nonairprint++;
             cout<<"ap: "<<airprint<<"  nonap: "<<nonairprint<<endl;   
             
             //TODO not very smart way to check but good for a start
             //Counts how many times we detected the artefact in the right zone. Needs to be > 4 so as to avoid false positives.
             if(nonairprint < 4 || airprint > 4)
             {
                 if(airprint > 4)
                 {
                     cout<<endl<<"----- AIRPRINT -----"<<endl<<endl;
                     //airprint = 0;
                     //nonairprint = 0;
                 }
                 else if(airprint == 0) nonairprint = 0;
             }
             else
             {
                 airprint = 0;
                 nonairprint = 0;
             }
             
         }
         mut.unlock();
         
         //std::this_thread::sleep_for(std::chrono::milliseconds(10)); //just in case, so as to give the thread time to lock the mutex
     }
     return 0;
 }
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 