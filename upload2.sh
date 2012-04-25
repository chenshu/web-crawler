#!/bin/bash

function upload {
    upfile=$1
    key="44444444444444444444444444444444"
    nsp_ts=`date +%s`
    nsp_fmt="JSON"
    nsp_key=`echo -n "$key""nsp_fmt$nsp_fmt""nsp_ts$nsp_ts"|md5sum -|cut -c -32|tr a-z A-Z`
    ret=`curl -F File=@$upfile \
        -F "nsp_fmt=$nsp_fmt" -F "nsp_ts=$nsp_ts" -F "nsp_key=$nsp_key" \
        -s "http://upload.dbank.com/upload/up.php"`
    echo -ne "$ret\n"
    succ=`echo $ret|grep '"success":"true"'|wc -l`
    #if [ $succ -ne 1 ]; then
    #    echo -ne "test_upload failed \n"
    #else
        #echo -ne "test_upload success \n"
    #fi
}

#files=$(awk -F'\t' '{print "arr["NR"]="$1}' /disk2/hiapk_upload)
#for file in $files
#do
#    echo $file
#done

function split()
{
    str=$1
    sep=$2

    OLD_IFS="$IFS"
    IFS=$sep
    arr=($str)
    IFS="$OLD_IFS"
    for s in ${arr[@]}
    do
        echo "$s" 
    done
}

for dir in $1/*
do
    for file in $dir/*
    do
        if [ -f $file ]; then
            echo -ne "$file\t"
            #arr=(`split $file "/"`)
            #num=${#arr[@]}
            #filename=${arr[$num-1]}
            #[[ ${filename/./} != ${filename} ]] && echo "yes" || echo "no"
            #[[ ${filename/./} != ${filename} ]] && echo -ne "$filename\t" || echo -ne "${filename:0:${#filename}-3}.${filename:${#filename}-3}\t"
            upload $file
        elif [ -d $file ]; then
            for f in $file/*
            do
                if [ -f $f ]; then
                    echo -ne "$f\t"
                    #arr=(`split $f "/"`)
                    #num=${#arr[@]}
                    #filename=${arr[$num-1]}
                    #[[ ${filename/./} != ${filename} ]] && echo "yes" || echo "no"
                    #[[ ${filename/./} != ${filename} ]] && echo -ne "$filename\t" || echo -ne "${filename:0:${#filename}-3}.${filename:${#filename}-3}\t"
                    upload $f
                fi
            done
        fi
    done
done
