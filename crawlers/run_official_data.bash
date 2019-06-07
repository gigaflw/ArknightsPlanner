FIELNAME=results/officials_`date "+%y%m%d_%H%M%S"`.jl
scrapy runspider officials.py -o $FIELNAME -s FEED_EXPORT_ENCODING='utf-8'

rm results/officials.jl 2>/dev/null
ln -s `realpath $FIELNAME` `realpath results/officials.jl`

echo "Official data updated: $FIELNAME"

# for test
# scrapy shell url