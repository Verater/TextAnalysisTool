'use strict';

const PORT = 5000;
const HOST = 'http://localhost:' + PORT + '/';
const services = {
  heartbeat: 'heartbeat',
  listDatasets: 'list_datasets',
  setMostRecentDataset: 'set_most_recent_dataset',
  getDataViewId: 'get_data_view_id',
  getTransformDefs: 'get_transform_defs',
  mostRecentDataView: 'most_recent_data_view',
  rawDataForDataView: 'raw_data_for_data_view',
  rawEntriesAndTagsForDataView: 'raw_entries_and_tags_for_data_view',
  transformDataView: 'transform_data_view',
  countUnique: 'count_unique',
  addTags: 'add_tags',
  removeTags: 'remove_tags',
  wordCountsOverTime: 'word_counts_over_time',
  tfIdfOverValuesData: 'tf_idf_over_values',
};

const config = {
  datasetsLoaded: false,
  activeDatasetHeight: 30,
};
const AVAILABLE_CHART_TYPES = ['bar', 'line', 'historicalWords'];


const PAYLOAD_KEY = "q";


const TransformType = {
  FILTER: 'filter',
  ENRICHMENT: 'enrich',
};
Object.freeze(TransformType);

const DEFAULT_USER_ID = 1;


function buildRequest(service, payload) {
  if (payload) {
    return HOST + service + '?' + PAYLOAD_KEY + '=' + JSON.stringify(payload);
  } else {
    return HOST + service;
  }
}

async function isServerAvailable() {
  const url = buildRequest(services.heartbeat);

  try {
    const response = await fetch(url);
    const result = await response.text();
    console.info('heartbeat', result);

  } catch (err) {
    console.log('Fetch Error:', err);
    handleNoServerFound();
  }
}

function handleNoServerFound() {
  const container = createDiv({
    style: {
      'margin-top': '30%',
    },
  });

  container.appendChild(createH1({text: 'server could not be found'}));
  container.appendChild(createDiv({text: 'please ensure your docker container is running'}));

  const errorScreen = createDiv({id: 'working'});

  errorScreen.appendChild(container);
  document.body.appendChild(errorScreen);
}

class App {
  static transformListWindowId = 'transformListWindow';
  static transformListTableId = 'transformListTable';

  static datasetWindowId = 'datasetWindow';
  static activeDatasetWindowId = 'activeDatasetWindow';
  static datasetSelectionWindowId = 'datasetSelectionWindow';

  static chartWindowId = 'chartWindow';
  static categoryWindowId = 'categoryWindow';
  static chart0CloseButtonId = 'chart0__closeButton';
  static chart1CloseButtonId = 'chart1__closeButton';
  static chart2CloseButtonId = 'chart2__closeButton';
  static chart3CloseButtonId = 'chart3__closeButton';

  static buildTransformWindowId = 'buildTransformWindow';
  static buildVisualizationWindowId = 'buildVisualizationWindow';
  static addTransformWindowId = 'addTransformWindow';
  static addFilterButtonId = 'addFilterButton';
  static addEnrichmentButtonId = 'addEnrichmentButton';
  static addVisualizationButtonId = 'addVisualizationButton';

  constructor() {
    this.userId = DEFAULT_USER_ID;

    this.datasetManager = new DatasetManager(
      App.datasetWindowId,
      App.activeDatasetWindowId,
      App.datasetSelectionWindowId,
    );

    this.tagManager = new TagManager();

    this.chartManager = new ChartManager(
      App.chartWindowId,
      App.categoryWindowId,
      App.chart0CloseButtonId,
      App.chart1CloseButtonId,
      App.chart2CloseButtonId,
      App.chart3CloseButtonId,
  