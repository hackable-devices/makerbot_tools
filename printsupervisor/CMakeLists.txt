cmake_minimum_required(VERSION 2.8)
project( opencv_test )
SET(COMPILE_DEFINITIONS -Werror)
if(UNIX)
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror -std=gnu++0x")
endif()
#OPENCV
find_package( OpenCV REQUIRED )
#FIND_LIBRARY(ZMQ_LIB libzmq PATHS /usr/include/ )

#camera driver lib
link_directories( /usr/lib/uv4l/uv4lext/armv6l )


FIND_PATH(ZMQ_INCLUDE_DIR zmq.hpp
    /usr/include
    /usr/local/include
    /usr/local/include/zmq
)

FIND_LIBRARY(ZMQ_LIBRARY NAMES zmq PATHS
    /usr/lib
    /usr/local/lib
    /usr/local/lib/zmq
)

# Copy the results to the output variables.
IF (ZMQ_INCLUDE_DIR AND ZMQ_LIBRARY)
        SET(ZMQ_LIBRARIES ${ZMQ_LIBRARY})
        SET(ZMQ_INCLUDE_DIRS ${ZMQ_INCLUDE_DIR})
        MESSAGE(STATUS "Found these zmq libs: ${ZMQ_LIBRARIES}")
ENDIF (ZMQ_INCLUDE_DIR AND ZMQ_LIBRARY)

link_directories( ${ZMQ_INCLUDE_DIR} )

add_executable(printsupervisor printsupervisor.cpp)
target_link_libraries(printsupervisor /usr/lib/uv4l/uv4lext/armv6l/libuv4lext.so ${OpenCV_LIBS} ${ZMQ_LIBRARY})
