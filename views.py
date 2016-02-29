from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import Person, Candidate, Thesis


def home(request):
    return render(request, 'etd_app/home.html')


def overview(request):
    return render(request, 'etd_app/overview.html')


def faq(request):
    return render(request, 'etd_app/faq.html')


def tutorials(request):
    return render(request, 'etd_app/tutorials.html')


def copyright(request):
    return render(request, 'etd_app/copyright.html')


@login_required
def register(request):
    from .forms import PersonForm, CandidateForm
    person_instance = None
    try:
        person_instance = Person.objects.get(netid=request.user.username)
    except Person.DoesNotExist:
        if 'orcid' in request.POST:
            try:
                person_instance = Person.objects.get(orcid=request.POST['orcid'])
            except Person.DoesNotExist:
                pass
    try:
        candidate_instance = Candidate.objects.get(person__netid=request.user.username)
    except Candidate.DoesNotExist:
        candidate_instance = None
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data[u'netid'] = request.user.username
        person_form = PersonForm(post_data, instance=person_instance)
        candidate_form = CandidateForm(post_data, instance=candidate_instance)
        if person_form.is_valid() and candidate_form.is_valid():
            person = person_form.save()
            candidate = candidate_form.save(commit=False)
            candidate.person = person
            candidate.save()
            return HttpResponseRedirect(reverse('candidate_home'))
    else:
        person_form = PersonForm(instance=person_instance)
        candidate_form = CandidateForm(instance=candidate_instance)
    return render(request, 'etd_app/register.html', {'person_form': person_form, 'candidate_form': candidate_form})


@login_required
def candidate_home(request):
    try:
        candidate = Candidate.objects.get(person__netid=request.user.username)
    except Candidate.DoesNotExist:
        return HttpResponseRedirect(reverse('register'))
    context_data = {'candidate': candidate}
    theses = Thesis.objects.filter(candidate=candidate)
    if theses:
        context_data['thesis'] = theses[0]
    return render(request, 'etd_app/candidate.html', context_data)


@login_required
def candidate_upload(request):
    from .forms import UploadForm
    try:
        candidate = Candidate.objects.get(person__netid=request.user.username)
    except Candidate.DoesNotExist:
        return HttpResponseRedirect(reverse('register'))
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save_upload(candidate)
            return HttpResponseRedirect(reverse('candidate_home'))
    else:
        form = UploadForm()
    return render(request, 'etd_app/candidate_upload.html', {'candidate': candidate, 'form': form})


@login_required
def candidate_metadata(request):
    from .forms import MetadataForm
    try:
        candidate = Candidate.objects.get(person__netid=request.user.username)
    except Candidate.DoesNotExist:
        return HttpResponseRedirect(reverse('register'))
    try:
        thesis = Thesis.objects.get(candidate=candidate)
    except Thesis.DoesNotExist:
        thesis = None
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['candidate'] = candidate.id
        form = MetadataForm(post_data, instance=thesis)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('candidate_home'))
    else:
        form = MetadataForm(instance=thesis)
    return render(request, 'etd_app/candidate_metadata.html', {'candidate': candidate, 'form': form})
