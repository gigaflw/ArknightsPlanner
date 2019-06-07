FIELNAME=results/droprates_`date "+%y%m%d_%H%M%S"`.jl
scrapy runspider penguin_statistic.py -o $FIELNAME.jl -s FEED_EXPORT_ENCODING='utf-8'

rm results/droprates.jl 2>/dev/null
ln -s `realpath $FIELNAME` `realpath results/droprates.jl`

echo "Droprate updated: $FIELNAME"

# for test
# scrapy shell url